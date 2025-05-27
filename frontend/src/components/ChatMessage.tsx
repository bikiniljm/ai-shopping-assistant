import React, { useState } from 'react'
import type { ChatMessage as ChatMessageType, Product, SearchParameters } from '../types/chat'
import { FaStar, FaStarHalf, FaUser, FaRobot, FaShippingFast, FaUndo, FaTrophy, FaCheck } from 'react-icons/fa'
import { FiUser } from 'react-icons/fi'
import { RiRobot2Fill } from 'react-icons/ri'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
    message: ChatMessageType;
    onExampleClick?: (text: string) => void;
}

function Badge({ type, label }: { type: string; label: string }) {
    const getIcon = () => {
        switch (type) {
            case 'free_shipping':
                return <FaShippingFast />;
            case 'free_returns':
                return <FaUndo />;
            case 'best_seller':
                return <FaTrophy />;
            case 'top_rated':
                return <FaStar />;
            default:
                return <FaCheck />;
        }
    };

    return (
        <div className="badge" title={label}>
            {getIcon()}
            <span>{label}</span>
        </div>
    );
}

function StarRating({ rating, count }: { rating: number | null; count: number }) {
    if (!rating) return null;
    
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    
    return (
        <div className="rating-container">
            <div className="star-rating">
                {[...Array(fullStars)].map((_, i) => (
                    <FaStar key={i} className="text-yellow-400" />
                ))}
                {hasHalfStar && <FaStarHalf className="text-yellow-400" />}
            </div>
            <span className="rating-count">({count.toLocaleString()})</span>
        </div>
    );
}

function SearchInfo({ params }: { params: SearchParameters }) {
    return (
        <div className="search-info">
            <div className="search-query">
                <strong>Searching for:</strong> {params.base_query}
                {params.color && ` in ${params.color}`}
                {params.brand && ` by ${params.brand}`}
            </div>
            
            <div className="search-details">
                {(params.age || params.gender || params.occasion) && (
                    <div className="search-audience">
                        <strong>For:</strong>
                        <ul>
                            {params.age && (
                                <li>Age: {params.age} years</li>
                            )}
                            {params.gender && (
                                <li>Gender: {params.gender}</li>
                            )}
                            {params.occasion && (
                                <li>Occasion: {params.occasion}</li>
                            )}
                        </ul>
                    </div>
                )}
                
                {params.filters && (
                    <div className="search-filters">
                        <strong>Filters:</strong>
                        <ul>
                            {params.filters.price_range && (
                                <li>
                                    💰 Price: 
                                    {params.filters.price_range.min ? ` $${params.filters.price_range.min}` : ' Any'} 
                                    -
                                    {params.filters.price_range.max ? ` $${params.filters.price_range.max}` : ' Any'}
                                </li>
                            )}
                            {params.filters.min_rating && (
                                <li>⭐ Min Rating: {params.filters.min_rating}</li>
                            )}
                            {params.filters.free_shipping && (
                                <li>🚚 Free Shipping</li>
                            )}
                            {params.filters.free_returns && (
                                <li>↩️ Free Returns</li>
                            )}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}

function ProductCard({ product }: { product: Product }) {
    const [imageLoaded, setImageLoaded] = useState(false);

    return (
        <div className="product-card">
            <div className="product-image-container">
                <img 
                    src={product.imageUrl} 
                    alt={product.title}
                    className={`product-image ${imageLoaded ? 'loaded' : 'loading'}`}
                    onLoad={() => setImageLoaded(true)}
                    onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = 'https://via.placeholder.com/300x300?text=Product+Image+Not+Available';
                        target.style.padding = '2rem';
                        setImageLoaded(true);
                    }}
                    loading="lazy"
                    decoding="async"
                />
                {product.badges && (
                    <div className="product-badges">
                        {product.badges.map((badge, index) => (
                            <Badge key={index} type={badge.type} label={badge.label} />
                        ))}
                    </div>
                )}
            </div>
            
            <div className="product-info">
                <h3 className="product-title">{product.title}</h3>
                
                <div className="product-rating">
                    <StarRating rating={product.rating} count={product.ratingCount} />
                </div>
                
                <div className="product-price">
                    <span className="price">{product.price_str}</span>
                    {product.delivery && (
                        <span className="delivery">{product.delivery}</span>
                    )}
                </div>

                <div className="product-source">
                    {product.source}
                </div>

                {product.features && product.features.length > 0 && (
                    <ul className="product-features">
                        {product.features.map((feature, index) => (
                            <li key={index}>{feature}</li>
                        ))}
                    </ul>
                )}
                
                <div className="product-footer">
                    <a 
                        href={product.link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="view-button"
                    >
                        View Details
                    </a>
                </div>
            </div>
        </div>
    );
}

function ProductGrid({ products }: { products: Product[] | undefined }) {
    if (!products?.length) return null;

    return (
        <div className="product-grid">
            {products.map((product, index) => (
                <ProductCard key={product.id || index} product={product} />
            ))}
        </div>
    );
}

function formatTextResponse(text: string): string {
    // Split into paragraphs
    const paragraphs = text.split('\n').filter(line => line.trim());
    
    // Format lists and bullet points
    const formattedParagraphs = paragraphs.map(para => {
        // Format follow-up questions
        if (para.includes('💡 To help you better:')) {
            return `\n---\n\n${para}\n`; // Add visual separator before follow-up
        }
        // Add markdown-style bullet points
        if (para.startsWith('•') || para.startsWith('-')) {
            return para;
        }
        // Format numbered lists
        if (/^\d+\./.test(para)) {
            return para;
        }
        // Format product titles (if not already in markdown)
        if (!para.includes('**') && para.includes(':')) {
            return para.replace(/^(.+?):/, '**$1**:');
        }
        return para;
    });

    return formattedParagraphs.join('\n\n');
}

export function ChatMessage({ message, onExampleClick }: Props) {
    const formattedText = message.isUser ? message.text : formatTextResponse(message.text);

    const handleExampleClick = (text: string) => {
        if (onExampleClick && text.startsWith('•')) {
            onExampleClick(text.substring(2).trim());
        }
    };

    return (
        <div className={`chat-message ${message.isUser ? 'user' : 'assistant'}`}>
            <div className="message-avatar">
                {message.isUser ? <FiUser size={24} /> : <RiRobot2Fill size={24} />}
            </div>
            
            <div className="message-content">
                {message.user_message?.type === 'image' ? (
                    <div className="message-image">
                        <img 
                            src={message.user_message.content.startsWith('blob:') || message.user_message.content.startsWith('data:') 
                                ? message.user_message.content 
                                : `http://localhost:8000${message.user_message.content}`} 
                            alt="Uploaded product" 
                            className="uploaded-image"
                        />
                    </div>
                ) : (
                    <div className="message-text">
                        {!message.isUser && message.text.includes('• ') ? (
                            <div>
                                {message.text.split('\n').map((line, index) => (
                                    <div key={index}>
                                        {line.startsWith('• ') ? (
                                            <div 
                                                className="example-question"
                                                onClick={() => handleExampleClick(line)}
                                            >
                                                {line}
                                            </div>
                                        ) : (
                                            <p className="markdown-paragraph">{line}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <ReactMarkdown 
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    p: ({node, children, ...props}) => {
                                        const text = String(children);
                                        if (text.includes('💡 To help you better:')) {
                                            return (
                                                <div className="follow-up-question">
                                                    <p {...props}>{children}</p>
                                                </div>
                                            );
                                        }
                                        return <p className="markdown-paragraph" {...props}>{children}</p>;
                                    },
                                    strong: ({node, ...props}) => <strong className="markdown-bold" {...props} />,
                                    em: ({node, ...props}) => <em className="markdown-italic" {...props} />,
                                    ul: ({node, ...props}) => <ul className="markdown-list" {...props} />,
                                    ol: ({node, ...props}) => <ol className="markdown-list" {...props} />,
                                    li: ({node, ...props}) => <li className="markdown-list-item" {...props} />,
                                    hr: ({node, ...props}) => <hr className="markdown-separator" {...props} />
                                }}
                            >
                                {formattedText}
                            </ReactMarkdown>
                        )}
                    </div>
                )}
                
                {message.search_params && (
                    <SearchInfo params={message.search_params} />
                )}
                
                {message.products && <ProductGrid products={message.products} />}
            </div>
        </div>
    );
} 