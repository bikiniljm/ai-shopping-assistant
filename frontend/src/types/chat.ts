export interface Product {
    id: string;
    title: string;
    description: string;
    price: number;
    price_str: string;  // Formatted price string
    link: string;
    imageUrl: string;
    rating: number | null;
    ratingCount: number;
    delivery: string;
    source: string;
    similarity_score?: number;
    features?: string[];  // Product features/highlights
    badges?: Array<{
        type: 'free_shipping' | 'free_returns' | 'best_seller' | 'top_rated';
        label: string;
    }>;
}

export interface QueryClassification {
    is_shopping: boolean;
    confidence: number;
    reasoning: string;
}

export interface SearchParameters {
    base_query: string;  // The base item or category being searched for
    filters?: {
        price_range?: {
            min?: number;
            max?: number;
        };
        min_rating?: number;
        free_shipping?: boolean;
        free_returns?: boolean;
    };
    properties?: Record<string, unknown>;  // Additional properties
}

export interface ChatMessage {
    text: string;
    image_url?: string;
    timestamp: string;
    isUser: boolean;
    recommendations?: Product[];
    classification?: QueryClassification;
    search_params?: SearchParameters;
    products?: Product[];
    user_message?: {
        type: 'image';
        content: string;
    };
}

export interface ChatResponse {
    text: string;
    timestamp: string;
    products: Product[];
    search_params?: SearchParameters;
    user_message?: {
        type: 'image';
        content: string;
    };
}

export interface ChatRequest {
    text: string;
    sessionId: string;
} 