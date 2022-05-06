import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, Normalizer
from sklearn.pipeline import Pipeline
from google.cloud import bigquery
import logging as log
logger = log.getLogger(__name__)
log.info('setting up the log for Bqpatent predictor')


class BqPatentPredictor:
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
        ct.fit([np.ones(64)])
        self.pipe = Pipeline(
            [('remove_useless_cols_in_pipeline', ct), ('standard_scaler', original_scaler), ('l2_norm', Normalizer())])
        self.bq_client = bigquery.Client()
        self.job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

    try:
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
              publication_number,
              custom_embedding,
              cosine_distance(custom_embedding) AS cosine_distance
            FROM `[dataset]`
            WHERE
              [where_statements]
              cosine_distance(custom_embedding) < [max_distance]
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

    except Exception as e:
        log.warning(e)


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
          publication_number,
          custom_embedding,
          cosine_distance(custom_embedding) AS cosine_distance
        FROM `[dataset]`
        WHERE
          [where_statements]
          cosine_distance(custom_embedding) < [max_distance]
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

    def get_corresponding_v1s(self, patent_list):

        if len(patent_list) == 1:
            p_list = f'("{patent_list[0]}")'
        else:
            p_list = str(tuple(patent_list))

        query = f"""SELECT publication_number, embedding_v1
        FROM `{self.bq_table}_cluster_partitioned`
        WHERE {self.where_statements} AND publication_number IN {p_list}

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
            publication_number,
            title,
            country_code,
            kind_code,
            filing_date,
            grant_date,
            abstract,
            embedding_v1,
            cosine_distance(embedding_v1) AS cosine_distance
          FROM `[dataset]`
          WHERE
            [where_statements]
            cosine_distance(embedding_v1) < [max_distance]
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

        X = self.pipe.transform(raw_embedding.reshape(1, -1))[0]
        if self.k > 1:
            custom_embedding_centroids_for_averaging = self.return_custom_embedding_centroids_for_averaging(X)
            X = np.stack(custom_embedding_centroids_for_averaging['custom_embedding'].values).mean(0)

        # print(X)

        custom_embedding_centroids_for_averaging = self.return_custom_embedding_centroids_for_averaging(X)

        patent_list = custom_embedding_centroids_for_averaging['publication_number'].to_list()
        corresponding_v1 = self.get_corresponding_v1s(patent_list)
        if self.k == 1:
            v1_centroid = corresponding_v1['embedding_v1'][0]
        else:
            v1_centroid = corresponding_v1['embedding_v1'].to_numpy().mean()

        patent_data = self.return_patent_data(v1_centroid)
        cost = self.costs * 500 / (1024 ** 4)
        self.costs = 0

        return patent_data, cost
