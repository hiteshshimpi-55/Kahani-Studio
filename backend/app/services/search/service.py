from app.integrations.databricks import VectorSearchQuery, similarity_search
from app.schemas.search.request import VectorSearchRequest
from app.schemas.search.response import VectorSearchHitResponse, VectorSearchResponse


class VectorSearchService:
    def search(self, request: VectorSearchRequest) -> VectorSearchResponse:
        result = similarity_search(
            VectorSearchQuery(
                query_text=request.query_text,
                columns=request.columns,
                num_results=request.num_results,
                filters=request.filters,
                query_type=request.query_type,
                endpoint_name=request.endpoint_name,
                index_name=request.index_name,
            )
        )
        hits = [VectorSearchHitResponse(fields=hit.raw) for hit in result.hits]
        return VectorSearchResponse(
            endpoint_name=result.endpoint_name,
            index_name=result.index_name,
            hits=hits,
            count=len(hits),
        )
