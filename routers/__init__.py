"""
Routers package for ICAP Enterprise
"""

# Check if colour-science is available before importing color router
try:
    import colour
    COLOUR_AVAILABLE = True
except (ImportError, ValueError):
    COLOUR_AVAILABLE = False

if COLOUR_AVAILABLE:
    from routers import color, vision, rag, agents, training, iot, auth, notifications, analytics, webhooks, compliance, mfa, cache, clients, models, knowledge_graph, reports
    __all__ = [
        'color',
        'vision',
        'rag',
        'agents',
        'training',
        'iot',
        'auth',
        'notifications',
        'analytics',
        'webhooks',
        'compliance',
        'mfa',
        'cache',
        'clients',
        'models',
        'knowledge_graph',
        'reports'
    ]
else:
    # If colour-science is not available, skip color router
    from routers import vision, rag, agents, training, iot, auth, notifications, analytics, webhooks, compliance, mfa, cache, clients, models, knowledge_graph, reports
    __all__ = [
        'vision',
        'rag',
        'agents',
        'training',
        'iot',
        'auth',
        'notifications',
        'analytics',
        'webhooks',
        'compliance',
        'mfa',
        'cache',
        'clients',
        'models',
        'knowledge_graph',
        'reports'
    ]
