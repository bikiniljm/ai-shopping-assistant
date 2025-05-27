import os
from dotenv import load_dotenv
from models.search import SearchParameters, SearchFilters, PriceRange, ProductSearcher

# Load environment variables
load_dotenv()


async def main():
    # Initialize the product searcher
    searcher = ProductSearcher()

    # Test cases with different search parameters
    test_cases = [
        SearchParameters(
            base_query="LEGO Star Wars sets",
            filters=SearchFilters(
                price_range=PriceRange(min=50, max=70), min_rating=4.0
            ),
        ),
        SearchParameters(
            base_query="educational toys",
            color="blue",
            age=6,
            gender="male",
            occasion="learning",
            filters=SearchFilters(
                price_range=PriceRange(min=20, max=50),
                min_rating=4.0,
                free_shipping=True,
            ),
            properties={"type": "science"},
        ),
        SearchParameters(
            base_query="princess toys",
            age=5,
            gender="female",
            filters=SearchFilters(
                price_range=PriceRange(max=30),
                free_returns=True,
                sellers=["amazon", "walmart"],
            ),
        ),
    ]

    for test_case in test_cases:
        print(f"\nTesting search with parameters:")
        print(test_case.model_dump_json(indent=2))
        print("-" * 80)

        # Search products
        products = await searcher.search_products(test_case)

        # Print results
        print(f"\nFound {len(products)} products:")
        for product in products:
            print(f"\n- {product.title}")
            print(f"  Price: {product.price_str}")
            if product.rating:
                print(f"  Rating: {product.rating}⭐ ({product.ratingCount} reviews)")
            print(f"  From: {product.source}")
            print(f"  Link: {product.link}")
        print("-" * 80)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
