"""
OpenTelemetry Distributed Tracing
==================================
Configuration and utilities for distributed tracing in ICAP.
"""

import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

logger = logging.getLogger("Tracing")

def setup_tracing(service_name: str = "icap-api", jaeger_host: str = "localhost", jaeger_port: int = 6831):
    """
    Setup OpenTelemetry tracing with Jaeger exporter.
    
    Args:
        service_name: Name of the service
        jaeger_host: Jaeger agent host
        jaeger_port: Jaeger agent port
    """
    # Check if tracing is enabled
    enable_tracing = os.environ.get("ICAP_ENABLE_TRACING", "false").lower() == "true"
    
    if not enable_tracing:
        logger.info("Distributed tracing is disabled. Set ICAP_ENABLE_TRACING=true to enable.")
        return
    
    try:
        # Create resource with service information
        resource = Resource.create({
            "service.name": service_name,
            "service.version": os.environ.get("ICAP_VERSION", "8.9.3"),
            "deployment.environment": os.environ.get("ICAP_ENVIRONMENT", "development")
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_host,
            agent_port=jaeger_port,
        )
        
        # Add batch span processor
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        logger.info(f"OpenTelemetry tracing enabled for {service_name}")
        logger.info(f"Jaeger exporter configured at {jaeger_host}:{jaeger_port}")
        
    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not installed: {e}")
        logger.info("Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger opentelemetry-instrumentation-fastapi")
    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}")

def instrument_fastapi(app):
    """
    Instrument FastAPI application with OpenTelemetry.
    
    Args:
        app: FastAPI application instance
    """
    enable_tracing = os.environ.get("ICAP_ENABLE_TRACING", "false").lower() == "true"
    
    if not enable_tracing:
        return
    
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")

def instrument_http_clients():
    """
    Instrument HTTP clients (httpx, requests) with OpenTelemetry.
    """
    enable_tracing = os.environ.get("ICAP_ENABLE_TRACING", "false").lower() == "true"
    
    if not enable_tracing:
        return
    
    try:
        HTTPXClientInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        logger.info("HTTP clients instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument HTTP clients: {e}")

def get_tracer(name: str = __name__):
    """
    Get a tracer instance.
    
    Args:
        name: Name of the tracer
        
    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)

class TracedOperation:
    """Context manager for tracing operations."""
    
    def __init__(self, operation_name: str, tracer_name: str = __name__):
        """
        Args:
            operation_name: Name of the operation
            tracer_name: Name of the tracer
        """
        self.operation_name = operation_name
        self.tracer = get_tracer(tracer_name)
        self.span = None
    
    def __enter__(self):
        self.span = self.tracer.start_as_current_span(self.operation_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type is not None:
                self.span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
            self.span.end()

def trace_function(tracer_name: str = __name__):
    """
    Decorator for tracing function execution.
    
    Args:
        tracer_name: Name of the tracer
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer(tracer_name)
            with tracer.start_as_current_span(func.__name__) as span:
                span.set_attribute("function.name", func.__name__)
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("function.success", False)
                    span.set_attribute("function.error", str(e))
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        return wrapper
    return decorator
