import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
from sklearn.utils.multiclass import unique_labels
from sklearn.metrics import euclidean_distances
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import normalize, StandardScaler, Normalizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import Pipeline


class numpy_distance_finding_object:

    def __init__(self, v1_df):
        self.embedding_object = np.stack(v1_df.to_numpy())
        self.length = self.embedding_object.shape[0]

    def get_embedding_from_indices(self, indices, mask):
        associated_v1_list = self.embedding_object[mask][indices]
        return associated_v1_list

    def find_indices_of_closest_vectors(self, v1_embedding, K_nearest, mask):
        similarities = cosine_similarity(v1_embedding.reshape(1, -1), self.embedding_object[mask])
        nearest_indices = np.flip(np.argsort(similarities)[0][-K_nearest:])
        return nearest_indices, similarities[0][nearest_indices]

    def get_k_nearest_patents(self, global_index_number, K, mask):
        # the global index number is converted to a local (for v1) index by subtracting 1, the corresponding v1 is then found
        associated_v1 = self.embedding_object[global_index_number - 1].reshape(1, -1)

        # masked
        nearest_indices, associated_distances = self.find_indices_of_closest_vectors(associated_v1, K, mask)

        # masked
        nearest_v1_list = self.get_embedding_from_indices(nearest_indices, mask)

        distance_frame = pd.DataFrame(nearest_v1_list, index=nearest_indices)
        distance_frame.index.name = "masked_indices"
        distance_frame = distance_frame.add_prefix("emb_")
        distance_frame.insert(0, "cosine_distance", 0)
        distance_frame["cosine_distance"] = associated_distances
        distance_frame.sort_values('cosine_distance', ascending=False, inplace=True)
        return distance_frame


class PatentClassifier(BaseEstimator, ClassifierMixin):

    def __init__(self):

        self.pipeline_ = None
        self.v1_frame_path = None
        self.metadata_frame_path = None
        self.custom_embedding_frame_path = None
        self.query = 'all'
        self.v1_mask = None
        self.custom_embedding_mask = None
        self.v1_length = None
        self.meta_data_length = None

    def fit(self, v1_frame_path, metadata_frame_path, custom_embedding_frame_path):

        # load the data
        self.v1_frame_path = v1_frame_path
        self.metadata_frame_path = metadata_frame_path
        self.custom_embedding_frame_path = custom_embedding_frame_path

        print('loading metadata')
        self.metadata = pd.read_parquet(metadata_frame_path, engine='pyarrow')
        print('loading v1 frame')
        self.v1_frame = pd.read_parquet(v1_frame_path, engine='pyarrow')
        print('loading custom_embedding')
        self.custom_embedding = pd.read_parquet(custom_embedding_frame_path, engine='pyarrow')
        print('finihed loading')

        good_cols = np.where(self.custom_embedding.std() != 0)[0]
        ct = ColumnTransformer([("remove_useless_cols", 'passthrough', good_cols)], remainder='drop')
        pipe = Pipeline(
            [('remove_useless_cols_in_pipeline', ct), ('standard_scaler', StandardScaler()), ('l2_norm', Normalizer())])
        self.custom_embedding = pd.DataFrame(pipe.fit_transform(self.custom_embedding),
                                             index=self.custom_embedding.index,
                                             columns=self.custom_embedding.columns[good_cols])

        self.v1_length = self.metadata.shape[0]
        self.meta_data_length = self.custom_embedding.shape[0]

        self.v1_mask = self.v1_length * [True]
        self.custom_embedding_mask = self.meta_data_length * [True]

        self.pipeline_ = pipe

        self.emb_ob = numpy_distance_finding_object(self.custom_embedding)

        self.v1_ob = numpy_distance_finding_object(self.v1_frame)

        return self

    def get_nearest_patents(self, custom_emb_vector,
                            k=10,
                            use_custom_embeddings=False,
                            n=1):

        nearest_indices, similarities = self.emb_ob.find_indices_of_closest_vectors(custom_emb_vector, k,
                                                                                    self.custom_embedding_mask)

        if n > 1:
            custom_emb_centroid = self.custom_embedding[self.custom_embedding_mask].iloc[nearest_indices].iloc[
                                  :n].mean().to_numpy()
            nearest_indices, similarities = self.emb_ob.find_indices_of_closest_vectors(custom_emb_centroid, k,
                                                                                        self.custom_embedding_mask)

        if not use_custom_embeddings:
            # we already know the relevant global name from the custom embeddings
            # probs here
            nearest_global_index = self.custom_embedding[self.custom_embedding_mask].iloc[[nearest_indices[0]]].index[0]
            print('nearest global index', nearest_global_index)
            v1_embedding_frame = self.v1_ob.get_k_nearest_patents(nearest_global_index, k, self.v1_mask)

            custom_emb_centroid = v1_embedding_frame.iloc[:n, 1:].mean().to_numpy()

            nearest_indices, similarities = self.v1_ob.find_indices_of_closest_vectors(custom_emb_centroid, k,
                                                                                       self.v1_mask)
            output = self.metadata[self.v1_mask].iloc[nearest_indices]
            output.loc[:, 'Similarity'] = similarities
            return (output)


        else:
            indices = self.custom_embedding[self.custom_embedding_mask].iloc[nearest_indices]
            output = self.metadata.loc[indices.index]
        output.loc[:, 'Similarity'] = similarities
        return (output)

    def query_with_all(df, query):
        if query == "all":
            return df
        return df.query(query)

    def predict(self, embedding, k=10, use_custom_embeddings=False, n=1, query='all', with_v1=False):

        if not query == self.query:
            # for caching
            if query == 'all':
                self.v1_mask = self.v1_length * [True]
                self.custom_embedding_mask = self.meta_data_length * [True]
                self.query = query
            else:
                v1_query_indices = self.metadata.query(query).index
                self.v1_mask = self.v1_frame.index.isin(v1_query_indices)
                self.custom_embedding_mask = self.custom_embedding.index.isin(v1_query_indices)
                self.query = query

        X = self.pipeline_.transform(np.array(embedding).reshape(1, -1))

        result = self.get_nearest_patents(X, k, use_custom_embeddings, n)
        if with_v1:
            result = pd.merge(result, self.v1_frame, left_index=True, right_index=True)

        return result

    def score(self):
        pass