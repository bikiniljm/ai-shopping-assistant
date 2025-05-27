from typing import List, Dict, Optional
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import json
import os
from enum import Enum
from .product import Product


class SortOption(Enum):
    """Enum for product sorting options"""

    RELEVANCE = "relevance"  # Default sorting by search relevance
    RATING = "rating"  # Sort by rating (high to low)
    RATING_COUNT = "rating_count"  # Sort by number of reviews (high to low)
    RATING_WEIGHTED = "rating_weighted"  # Sort by rating weighted by review count
    PRICE_LOW = "price_low"  # Sort by price (low to high)
    PRICE_HIGH = "price_high"  # Sort by price (high to low)


def get_sorted_products(
    products: List[Product],
    sort_by: SortOption = SortOption.RELEVANCE,
    limit: Optional[int] = None,
) -> List[Product]:
    """
    Sort products by the specified option.

    Args:
        products: List of products to sort
        sort_by: SortOption enum specifying sort method
        limit: Optional maximum number of products to return

    Returns:
        List of sorted products, optionally limited to specified count
    """
    sorted_products = products.copy()  # Don't modify original list

    if sort_by == SortOption.RELEVANCE:
        # Keep original order (assumed to be by relevance)
        pass

    elif sort_by == SortOption.RATING:
        # Sort by rating high to low, handle None ratings
        sorted_products.sort(
            key=lambda p: (p.rating if p.rating is not None else -1), reverse=True
        )

    elif sort_by == SortOption.RATING_COUNT:
        # Sort by number of reviews high to low
        sorted_products.sort(
            key=lambda p: p.ratingCount if p.ratingCount is not None else 0,
            reverse=True,
        )

    elif sort_by == SortOption.RATING_WEIGHTED:
        # Wilson score interval sort - balances rating with number of reviews
        def wilson_score(product: Product) -> float:
            if not product.rating or not product.ratingCount:
                return -1

            # Convert 5-star rating to proportion (0-1)
            pos = (product.rating / 5.0) * product.ratingCount
            n = product.ratingCount

            # Constants for 95% confidence
            z = 1.96
            zsqr = z * z

            # Wilson score calculation
            numerator = (pos + zsqr / 2) / n
            denominator = 1 + zsqr / n

            return numerator / denominator

        sorted_products.sort(key=wilson_score, reverse=True)

    elif sort_by == SortOption.PRICE_LOW:
        # Sort by price low to high, handle None prices
        sorted_products.sort(
            key=lambda p: float(p.price) if p.price is not None else float("inf")
        )

    elif sort_by == SortOption.PRICE_HIGH:
        # Sort by price high to low, handle None prices
        sorted_products.sort(
            key=lambda p: float(p.price) if p.price is not None else -1, reverse=True
        )

    # Apply limit if specified
    if limit is not None:
        sorted_products = sorted_products[:limit]

    return sorted_products


class ProductStore:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_store = None
        self.products: List[Product] = []

    def _create_product_document(self, product: Dict) -> str:
        """Create a searchable document from a product."""
        return f"""
        Product: {product.get("title", "")}
        Price: {product.get("price", "")}
        Source: {product.get("source", "")}
        Rating: {product.get("rating", "N/A")} ({product.get("ratingCount", 0)} reviews)
        Delivery: {product.get("delivery", "")}
        Description: From {product.get("source", "")}
        URL: {product.get("link", "")}
        """

    def add_products(self, products: List[Product]):
        """Add products to the vector store."""
        self.products.extend(products)

        # Create documents from products
        documents = [self._create_product_document(product) for product in products]

        # Create or update vector store
        if self.vector_store is None:
            self.vector_store = FAISS.from_texts(
                documents,
                self.embeddings,
                metadatas=[{"index": i} for i in range(len(documents))],
            )
        else:
            self.vector_store.add_texts(
                documents,
                metadatas=[
                    {"index": i + len(self.products)} for i in range(len(documents))
                ],
            )

    def search_products(self, query: str, k: int = 3) -> List[Dict]:
        """Search for products using semantic similarity."""
        if not self.vector_store or not self.products:
            return []

        # Perform similarity search
        results = self.vector_store.similarity_search_with_score(query, k=k)

        # Get original products using metadata indices
        relevant_products = []
        for doc, score in results:
            index = doc.metadata.get("index")
            if index is not None and 0 <= index < len(self.products):
                product = self.products[index]
                # Add similarity score to product
                product_with_score = {**product, "similarity_score": float(score)}
                relevant_products.append(product_with_score)

        return relevant_products

    def clear(self):
        """Clear all products and reset the vector store."""
        self.products = []
        self.vector_store = None

    def clear_products(self):
        """Clear all products from the store"""
        self.products = []
