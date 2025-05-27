import os
import json
import base64
from typing import Dict, List
from openai import AsyncOpenAI
from langchain_core.messages import HumanMessage
from langchain.memory import ConversationBufferMemory
from datetime import datetime
from models.search import SearchParameters, ProductSearcher
from models.product import Product
from models.conversation import ConversationContext, ConversationState
from models.product_store import get_sorted_products, SortOption


class TextMessageHandler:
    def __init__(self):
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

        # Dictionary to store conversation contexts and memory for each session
        self.sessions: Dict[
            str, tuple[ConversationContext, ConversationBufferMemory]
        ] = {}

        # Initialize product searcher
        self.product_searcher = ProductSearcher()

    def _get_or_create_session(
        self, session_id: str
    ) -> tuple[ConversationContext, ConversationBufferMemory]:
        """Get or create a new session context and memory."""
        if session_id not in self.sessions:
            self.sessions[session_id] = (
                ConversationContext(),
                ConversationBufferMemory(
                    memory_key="chat_history", return_messages=True
                ),
            )
        return self.sessions[session_id]

    async def generate_product_response(
        self,
        products: List[Product],
        search_params: SearchParameters,
        initial_response: str,
    ) -> str:
        """
        Use LLM to generate a personalized response explaining product recommendations
        """
        # Create a summary of search parameters for context
        param_summary = {
            "query": search_params.base_query,
            "filters": search_params.filters.dict() if search_params.filters else None,
            "sort_by": search_params.sort_by.value if search_params.sort_by else None,
        }

        # Format products for LLM context
        product_details = []
        for i, product in enumerate(products, 1):
            product_details.append(
                {
                    "number": i,
                    "title": product.title,
                    "price": product.price_str,
                    "rating": product.rating,
                    "review_count": product.ratingCount,
                    "store": product.source,
                    "link": product.link,
                    "features": {
                        "has_price": product.price is not None,
                        "has_rating": product.rating is not None,
                        "has_reviews": product.ratingCount is not None
                        and product.ratingCount > 0,
                    },
                }
            )

        # Create the prompt for the LLM
        system_prompt = """You are an enthusiastic and helpful shopping assistant who loves finding the perfect products for customers.
        Your role is to:
        1. Start with a brief, friendly greeting
        2. Present each product with ONLY its title and a personalized reason
        3. Ask ONE follow-up question to improve future recommendations, considering any previous questions asked

        STRICT PRODUCT FORMAT:
        For each product, use exactly this format:
        
        **[Product Title]**
        ✨ [personalized reason focusing on features and user preferences]

        DO NOT include:
        - Price information
        - Rating or review information
        - Store/seller information
        - Links or calls to action
        - Technical specifications
        - Additional product details
        
        After presenting all products:
        1. Add a line break
        2. Add "**💡 To help you better:**"
        3. Ask ONE natural follow-up question based on initial response and current param_summary:

        Example Contextual Questions:
        - "Would you prefer to see options sorted by customer ratings or price?"
        - "What's your budget range for these items?"
        - "Would you like to see more premium options with additional features?"
        - "Do you have a specific style preference between [feature A] and [feature B] shown?"
        - "What size are you looking for in these items?"

        Remember:
        - Keep explanations focused on how features benefit the user
        - Use natural, conversational language
        - Maintain consistent formatting for each product
        - Start each reason with the ✨ icon
        - Only include title and personalized reason
        - Make the help question bold with **💡 To help you better:**
        - Choose follow-up questions that will most help refine future recommendations
        - Avoid repeating questions that were already asked in the initial response"""

        user_prompt = f"""
        Initial response: {initial_response}
        
        Current user preferences: {json.dumps(param_summary, indent=2)}
        
        Available products: {json.dumps(product_details, indent=2)}
        
        Generate a response following the STRICT PRODUCT FORMAT:
        1. Brief greeting
        2. For each product:
           **[Product Title]**
           ✨ [reason]
        3. Bold help question: **💡 To help you better**: **[contextual question based on current preferences, shown products, and avoiding questions from initial response]**
        
        DO NOT include any price, rating, store information, or additional details."""

        # Get response from OpenAI
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content

    def failover_response(self, products: List[Product]) -> str:
        """
        Format product results for chat display
        """
        if not products:
            return "I couldn't find any products matching your criteria. Would you like to try with different preferences?"

        # Use the basic format as fallback in case of LLM errors
        formatted_text = "Here are some products that match your requirements:\n\n"

        for i, product in enumerate(products, 1):
            formatted_text += f"{i}. {product.title}\n"

        return formatted_text

    async def handle_message(self, message: str, session_id: str) -> Dict:
        """
        Main handler for processing text messages.
        Returns only the fields used by the frontend:
        - text: The response text
        - timestamp: ISO format timestamp
        - products: List of products (if any)
        - search_params: Search parameters (if any)
        """
        try:
            # Get or create session context and memory
            context, memory = self._get_or_create_session(session_id)

            # Get chat history for context
            chat_history = memory.load_memory_variables({})["chat_history"]
            formatted_history = [
                {
                    "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                    "content": msg.content,
                }
                for msg in chat_history
            ]

            # Analyze user input using conversation context
            (
                new_state,
                search_params,
                initial_response,
            ) = await context.analyze_user_input(message, formatted_history)

            # Handle state transitions
            if new_state in [ConversationState.INITIAL, ConversationState.ENDED]:
                # Clear conversation memory for new/reset search or ended conversation
                memory.clear()

            # Update conversation memory with properly formatted messages
            memory.chat_memory.add_user_message(message)

            # Base response structure
            response = {
                "text": initial_response,
                "timestamp": datetime.now().isoformat(),
                "products": [],
                "search_params": None,
            }

            # If we're ready to search
            if (
                new_state == ConversationState.READY_TO_SEARCH
                and search_params
                and search_params.base_query
            ):
                # Get all matching products
                products = await self.product_searcher.search_products(search_params)

                limit_return = 3
                # Sort products if sort option is specified
                if search_params.sort_by:
                    return_products = get_sorted_products(
                        products=products,
                        sort_by=search_params.sort_by,
                        limit=limit_return,
                    )
                else:
                    return_products = products[:limit_return]

                try:
                    # Try to generate personalized response using LLM
                    response_text = await self.generate_product_response(
                        return_products, search_params, initial_response
                    )
                except Exception as e:
                    print(f"Error generating LLM response: {e}")
                    # Fall back to basic formatting if LLM fails
                    response_text = self.failover_response(return_products)

                response.update(
                    {
                        "text": response_text,
                        "products": [
                            product.model_dump() for product in return_products
                        ],
                        "search_params": search_params.model_dump(),
                    }
                )

            # Update conversation memory with response
            memory.chat_memory.add_ai_message(response["text"])
            return response

        except Exception as e:
            print(f"Error handling message: {e}")
            # Clear memory on error
            if session_id in self.sessions:
                self.sessions[session_id][1].clear()
            error_response = "I apologize, but I encountered an error while processing your request. Let's start over. What are you looking for?"
            return {
                "text": error_response,
                "timestamp": datetime.now().isoformat(),
                "products": [],
                "search_params": None,
            }

    async def handle_image_search(
        self, image_path: str, image_url: str, session_id: str
    ) -> Dict[str, any]:
        """
        Analyze an image and extract detailed information about the product
        Args:
            image_path: Path to the uploaded image file
            image_url: URL to access the uploaded image
            session_id: Session ID for conversation context
        Returns:
            Dict containing analysis results and image URL for display
        """
        try:
            # Get or create session context and memory
            context, memory = self._get_or_create_session(session_id)

            # Read and encode image file
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                base64_image = base64.b64encode(image_data).decode("utf-8")
                data_url = f"data:image/jpeg;base64,{base64_image}"

            # Get image analysis from OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a shopping assistant specialized in analyzing product images.
                        Your task is to describe the product in a natural, conversational way that can be used for product search.
                        Focus on key details that would be useful for finding similar products:
                        - Product type and key attributes (combined into a hyphenated base_query)
                        - Potential use cases
                        
                        Format your response as a JSON object with:
                        - base_query: Hyphenated string combining product type and key attributes (e.g., "black-leather-crossbody-handbag", "blue-running-shoes-with-mesh", "vintage-blue-denim-jacket")
                        
                        Example:
                        {
                            "base_query": "red-leather-crossbody-handbag-with-gold-chain",
                        }
                        """,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please analyze this product image and describe what you see:",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url,
                                },
                            },
                        ],
                    },
                ],
                response_format={"type": "json_object"},
                max_tokens=150,
            )

            # Extract the analysis from the response
            result = json.loads(response.choices[0].message.content)

            # Format a natural language description from the hyphenated base_query
            description = result["base_query"].replace("-", " ")

            # Create a message indicating what was found in the image
            image_message = f"I found {description} in the image. Would you like me to search for similar products?"

            # Update conversation memory with assistant's response
            memory.chat_memory.add_ai_message(image_message)

            return {
                "success": True,
                "text": image_message,
                "error": None,
                "user_message": {"type": "image", "content": image_url},
            }

        except Exception as e:
            print(f"Error in image analysis: {e}")
            # Reset conversation and memory on error
            if session_id in self.sessions:
                self.sessions[session_id][1].clear()
            error_response = "I apologize, but I encountered an error while analyzing the image. Could you please try uploading it again or describe what you're looking for?"
            return {
                "success": False,
                "text": error_response,
                "error": str(e),
                "user_message": None,
            }
