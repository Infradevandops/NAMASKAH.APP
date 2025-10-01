class SearchService:
    """
    Service for ranking search results.
    """

    def rank_results(self, query: str, results: list) -> list:
        """
        Rank search results based on a relevance score.

        Args:
            query: The search query.
            results: A list of search results.

        Returns:
            A list of ranked search results.
        """
        ranked_results = []
        for result in results:
            score = self.calculate_relevance(query, result)
            result['relevance'] = score
            ranked_results.append(result)

        return sorted(ranked_results, key=lambda x: x['relevance'], reverse=True)

    def calculate_relevance(self, query: str, result: dict) -> float:
        """
        Calculate the relevance score for a single result.

        Args:
            query: The search query.
            result: A single search result.

        Returns:
            The relevance score.
        """
        score = 0.0
        title = result.get('title', '').lower()
        content = result.get('content', '').lower()
        query = query.lower()

        if query in title:
            score += 1.0
        if query in content:
            score += 0.5

        return score
