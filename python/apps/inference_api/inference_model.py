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
from google.cloud import bigquery

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


class bqPatentPredictor:
    def __init__(self, bq_table, k=1, use_custom_embeddings=False, n=20, max_distance=0.3, where_statements=None,
                 est_file_path=None):
        self.bq_table = bq_table
        self.k = k
        self.use_custom_embeddings = use_custom_embeddings
        self.n = n
        self.max_distance = max_distance
        self.where_statements = where_statements
        self.costs = 0

        out = pd.read_csv(est_file_path, index_col=0)
        good_cols = np.where(out.loc['stdev'] >= 0.01)[0]
        original_scaler = StandardScaler()
        original_scaler.mean_ = out.loc['mean'].values[good_cols]
        original_scaler.scale_ = out.loc['stdev'].values[good_cols]
        original_scaler.n_samples_seen_ = 1
        ct = ColumnTransformer([("remove_useless_cols", 'passthrough', good_cols)], remainder='drop')
        ct.fit([np.ones(64)]);
        self.pipe = Pipeline(
            [('remove_useless_cols_in_pipeline', ct), ('standard_scaler', original_scaler), ('l2_norm', Normalizer())])
        self.bq_client = bigquery.Client()
        self.job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

    def return_custom_embedding_centroids_for_averaging(self, X):

        embedding_query_string = r'''
      #standardSQL

      CREATE TEMPORARY FUNCTION cosine_distance(patent ARRAY<FLOAT64>)
      RETURNS FLOAT64
      LANGUAGE js AS """
        var custom_vector = [custom_vector];

        var dotproduct = 0;
        var A = 0;
        var B = 0;
        for (i = 0; i < patent.length; i++){
          dotproduct += (patent[i] * custom_vector[i]);
          A += (patent[i]*patent[i]);
          B += (custom_vector[i]*custom_vector[i]);
        }
        A = Math.sqrt(A);
        B = Math.sqrt(B);
        var cosine_distance = 1 - (dotproduct)/(A)*(B);
        return cosine_distance;
      """;

        SELECT
          ced.publication_number,
          ced.custom_embedding,
          cosine_distance(ced.custom_embedding) AS cosine_distance
        FROM `[dataset]` ced
        WHERE 
          [where_statements]
          cosine_distance(ced.custom_embedding) < [max_distance]
        ORDER BY
          cosine_distance
        LIMIT [max_results]
    '''

        if self.where_statements != None:
            where_statements = self.where_statements + ' AND'
        else:
            where_statements = ''

        query_ = embedding_query_string.replace('[dataset]',
                                                f"{self.bq_table}_custom_embedding")
        query_ = query_.replace('[custom_vector]',
                                str(X.tolist()))
        query_ = query_.replace('[max_distance]',
                                str(self.max_distance))
        query_ = query_.replace('[where_statements]',
                                where_statements)
        query_ = query_.replace('[max_results]',
                                str(self.k))

        print(query_)
        self.accumulate_costs(query_)
        result = pd.read_gbq(query_)
        return (result)

    def get_corresponing_v1s(self, patent_list):

        if len(patent_list) == 1:
            p_list = f'("{patent_list[0]}")'
        else:
            p_list = str(tuple(patent_list))

        query = f"""SELECT ov1.publication_number, ov1.embedding_v1
        FROM `{self.bq_table}_cluster_partitioned` ov1
        WHERE ov1.publication_number IN {p_list}

        LIMIT {self.n}
        """

        print(query)

        result = pd.read_gbq(query)
        self.accumulate_costs(query)
        return (result)

    def return_patent_data(self, v1_centroid):
        embedding_query_string = '''CREATE TEMPORARY FUNCTION cosine_distance(patent ARRAY<FLOAT64>)
        RETURNS FLOAT64
        LANGUAGE js AS """
          var custom_vector = [custom_vector];

          var dotproduct = 0;
          var A = 0;
          var B = 0;
          for (i = 0; i < patent.length; i++){
            dotproduct += (patent[i] * custom_vector[i]);
            A += (patent[i]*patent[i]);
            B += (custom_vector[i]*custom_vector[i]);
          }
          A = Math.sqrt(A);
          B = Math.sqrt(B);
          var cosine_distance = 1 - (dotproduct)/(A)*(B);
          return cosine_distance;
        """;

          SELECT
            ced.publication_number,
            ced.title,
            ced.country_code,
            ced.kind_code,
            ced.abstract,
            ced.embedding_v1,
            cosine_distance(ced.embedding_v1) AS cosine_distance
          FROM `[dataset]` ced
          WHERE 
            [where_statements]
            cosine_distance(ced.embedding_v1) < [max_distance]
          ORDER BY
            cosine_distance
          LIMIT [max_results]'''

        if self.where_statements != None:
            where_statements = self.where_statements + ' AND'
        else:

            where_statements = ''

            query_ = embedding_query_string.replace('[dataset]',
                                                    f"{self.bq_table}_cluster_partitioned")
            query_ = query_.replace('[custom_vector]',
                                    str(v1_centroid.tolist()))
            query_ = query_.replace('[max_distance]',
                                    str(self.max_distance))
            query_ = query_.replace('[where_statements]',
                                    where_statements)
            query_ = query_.replace('[max_results]',
                                    str(self.n))

            result = pd.read_gbq(query_)
            self.accumulate_costs(query_)
        return (result)

    def accumulate_costs(self, q):

        query_job = self.bq_client.query(q, job_config=self.job_config)
        self.costs += query_job.total_bytes_processed

    def bq_get_nearest_patents(self, raw_embedding):
        # n is number of patents to return
        # k is number of nearest custom embedding patents to take a centre from
        X = self.pipe.transform(raw_embedding.reshape(1, -1))[0]
        if self.k > 1:
            custom_embedding_centroids_for_averaging = self.return_custom_embedding_centroids_for_averaging(X)
            X = np.stack(custom_embedding_centroids_for_averaging['custom_embedding'].values).mean(0)

        # print(X)

        custom_embedding_centroids_for_averaging = self.return_custom_embedding_centroids_for_averaging(X)

        patent_list = custom_embedding_centroids_for_averaging['publication_number'].to_list()
        corresponding_v1 = self.get_corresponing_v1s(patent_list)
        if self.k == 1:
            v1_centroid = corresponding_v1['embedding_v1'][0]
        else:
            v1_centroid = corresponding_v1['embedding_v1'].to_numpy().mean()

        patent_data = self.return_patent_data(v1_centroid)
        cost = self.costs * 500 / (1024 ** 4)
        self.costs = 0

        return patent_data, cost
