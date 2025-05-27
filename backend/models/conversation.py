from typing import Optional, Dict, List, Tuple
from pydantic import BaseModel, Field
from enum import Enum
import json
from openai import AsyncOpenAI
import os
from .search import SearchParameters
from .product_store import SortOption
import asyncio


class ConversationState(Enum):
    INITIAL = "initial"  # Initial state when conversation starts or resets
    COLLECTING_INFO = "collecting_info"  # Collecting any missing information
    READY_TO_SEARCH = "ready_to_search"  # Have enough info to perform search
    ENDED = "ended"  # Conversation has ended


class ConversationContext(BaseModel):
    """Tracks the state and collected information during a search conversation"""

    # OpenAI client for analysis
    _client: Optional[AsyncOpenAI] = None

    async def analyze_user_input(
        self, message: str, chat_history: List[Dict[str, str]]
    ) -> Tuple[ConversationState, Optional[SearchParameters], str]:
        """Analyze user input and return the new state, search parameters, and response.

        Returns:
            Tuple containing:
            - ConversationState: The new conversation state
            - Optional[SearchParameters]: Updated search parameters (None if not applicable)
            - str: Response message to send to the user
        """
        try:
            if not self._client:
                self._client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

            # Run state analysis and parameter extraction in parallel
            state_task = asyncio.create_task(
                self._analyze_conversation_state(message, chat_history)
            )
            params_task = asyncio.create_task(
                self._extract_search_parameters(message, chat_history)
            )

            # Wait for both tasks to complete
            state_result, search_params = await asyncio.gather(
                state_task, params_task, return_exceptions=True
            )

            # Handle any exceptions from the parallel tasks
            if isinstance(state_result, Exception):
                print(f"Error in state analysis: {state_result}")
                state_result = {
                    "state": "collecting_info",
                    "response": "I'm having trouble understanding that. Could you please rephrase?",
                }

            if isinstance(search_params, Exception):
                print(f"Error in parameter extraction: {search_params}")
                search_params = SearchParameters(base_query=None)

            # Get the new state
            new_state = ConversationState(state_result["state"])
            print(f"State Result: {state_result}")
            print(f"Search params: {search_params}")

            # Handle terminal states first
            if new_state == ConversationState.ENDED:
                return new_state, None, state_result["response"]
            elif new_state == ConversationState.INITIAL:
                return new_state, None, state_result["response"]

            # Process search parameters for active states
            # if new_state in [
            #     ConversationState.COLLECTING_INFO,
            #     ConversationState.READY_TO_SEARCH,
            # ]:
            #     # Update state based on extracted parameters
            #     final_state = (
            #         ConversationState.READY_TO_SEARCH
            #         if search_params.base_query
            #         else ConversationState.COLLECTING_INFO
            #     )
            #     response = (
            #         f"I understand you're looking for {search_params.base_query}"
            #         + (
            #             f" with these preferences: {search_params.filters}"
            #             if search_params.filters
            #             else ""
            #         )
            #     )
            #     return new_state, search_params, state_result["response"]
            # else:
            return new_state, search_params, state_result["response"]

        except Exception as e:
            print(f"Error analyzing user input: {e}")
            return (
                ConversationState.COLLECTING_INFO,
                None,
                "I'm having trouble understanding that. Could you please rephrase?",
            )

    async def _analyze_conversation_state(
        self, message: str, chat_history: List[Dict[str, str]]
    ) -> Dict:
        """Analyze the conversation state and determine next action"""

        system_prompt = """You are a shopping assistant helping to understand conversation flow.
        Your role is to analyze messages and determine the appropriate conversation state.

        IMPORTANT GUIDELINES:
        - For greetings or general messages without product mentions:
          * Set state to "collecting_info"
          * Provide a welcoming response asking what they're looking for
        
        - For shopping requests or product selections:
          * When user provides ANY of these:
            - Specific product name/category (e.g. "pink dress shoes", "laptop")
            - Clear product attributes (e.g. "size 4", "for girls")
            - Product preferences (e.g. "highly rated", "under $50")
            → Set state to "ready_to_search"
            → Respond with enthusiasm about finding matching items
          * ONLY set to "collecting_info" when:
            - User gives no product info at all
            - User asks for general shopping help
            - User needs guidance on product types
        
        - For dissatisfaction or explicit new search requests:
          * Set state to "initial"
          * Ask what they'd like to look for instead
        
        - ONLY set state to "ended" when:
          * User explicitly ends the conversation (e.g., "goodbye", "thanks, bye")
          * User clearly indicates no more help needed
          * Do NOT end just because user shows interest in a product

        EXAMPLES:
        User: "I'm looking for pink dress shoes for my daughter"
        → state: "ready_to_search" (has product type and attributes)
        
        User: "Show me highly rated ones"
        → state: "ready_to_search" (has clear preference)
        
        User: "I need help shopping"
        → state: "collecting_info" (no specific product mentioned)
        
        User: "What kinds of shoes do you have?"
        → state: "collecting_info" (needs guidance on types)
        
        User: "Thanks for your help, goodbye!"
        → state: "ended" (explicit end)

        Your response should be a JSON object with these fields:
        {
            "state": "initial/collecting_info/ready_to_search/ended",
            "response": "string (your helpful response to the user)"
        }"""

        messages = [{"role": "system", "content": system_prompt}]

        # Add chat history and current message
        messages.extend(chat_history)
        messages.append({"role": "user", "content": message})

        response = await self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        return json.loads(response.choices[0].message.content)

    async def _extract_search_parameters(
        self, message: str, chat_history: List[Dict[str, str]]
    ) -> SearchParameters:
        """Extract search parameters from user message"""
        try:
            system_prompt = """Your role is to analyze user messages and extract structured search parameters.

            You must output a valid SearchParameters object with:
            - base_query: Required main search term combining attributes with hyphens
            - filters: Optional SearchFilters object with:
              - price_range: Optional PriceRange with min/max
              - min_rating: Optional float between 1-5
              - free_shipping: Optional boolean
              - free_returns: Optional boolean
            - sort_by: Optional SortOption enum value for sorting products:
              - "relevance": Default sorting by search relevance (DO NOT SET THIS EXPLICITLY)
              - "rating": ONLY set when user explicitly asks to sort by rating
              - "rating_count": ONLY set when user explicitly asks to sort by number of reviews
              - "rating_weighted": ONLY set when user explicitly asks for best/most popular/recommended
              - "price_low": ONLY set when user explicitly asks to sort by price low to high
              - "price_high": ONLY set when user explicitly asks to sort by price high to low

            Guidelines:
            1. base_query: Combine attributes with hyphens
               e.g. "black-leather-laptop-bag-15-inch"
            
            2. price_range: Extract from:
               - Numbers: "under $50" → max: 50
               - Ranges: "$100-200" → min: 100, max: 200
               - Terms: "budget" → max: 50, "premium" → min: 300
            
            3. min_rating: Map from:
               - Stars: "4 stars" → 4.0
               - Terms: "best" → 4.0, "good" → 3.0
            
            4. Set shipping/returns flags if explicitly requested

            5. sort_by: ONLY set when user EXPLICITLY requests a specific sort order:
               - DO NOT set sort_by if user doesn't mention sorting
               - DO NOT default to "relevance" - leave as null
               - Examples of explicit sort requests:
                 "sort by rating" → "rating"
                 "show cheapest first" → "price_low"
                 "most expensive first" → "price_high"
                 "best rated" → "rating"
                 "most reviews" → "rating_count"
                 "most popular/recommended" → "rating_weighted"

            IMPORTANT: Consider the entire conversation context when extracting parameters.
            - Update or refine parameters based on new information
            - Maintain previously specified preferences unless explicitly changed
            - Combine related information from multiple messages"""

            messages = [{"role": "system", "content": system_prompt}]

            # Add chat history and current message
            messages.extend(chat_history)
            messages.append({"role": "user", "content": message})

            # print(f"_extract_search_parameters-Messages: {messages}")

            response = await self._client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=messages,
                response_format=SearchParameters,
                temperature=0.7,
            )

            return response.choices[0].message.parsed

        except Exception as e:
            print(f"Error extracting search parameters: {e}")
            return SearchParameters(base_query=None)
