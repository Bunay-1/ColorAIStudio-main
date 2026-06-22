"""
Integration Tests for Color Engine
==================================
Тестове за интеграция на Color Engine с други компоненти.
"""

import pytest
import numpy as np
from color_engine import ColorEngine
from ai_color_analysis import AIColorAnalysis

@pytest.fixture
def color_engine():
    """Fixture за Color Engine."""
    return ColorEngine()

@pytest.fixture
def ai_analysis():
    """Fixture за AI Color Analysis."""
    return AIColorAnalysis()

def test_color_engine_delta_e_calculation(color_engine):
    """Тест за изчисляване на Delta E с различни методи."""
    lab_sample = [50.0, 10.0, 20.0]
    lab_standard = [50.5, 10.5, 20.5]
    
    # Test different methods
    for method in ["CIE1976", "CIE1994", "CIE2000", "CMC"]:
        de = color_engine.calculate_delta_e(lab_sample, lab_standard, method)
        assert de > 0
        assert isinstance(de, (int, float))
        assert not np.isnan(de)

def test_color_engine_ral_matching(color_engine):
    """Тест за намиране на най-близък RAL цвят."""
    lab_sample = [50.0, 10.0, 20.0]
    closest_ral = color_engine.get_closest_ral(lab_sample)
    
    assert closest_ral is not None
    assert isinstance(closest_ral, dict)
    assert "name" in closest_ral
    assert "lab" in closest_ral

def test_color_engine_spectral_conversion(color_engine):
    """Тест за конвертиране на Lab към спектрални данни."""
    lab_sample = [50.0, 10.0, 20.0]
    sd = color_engine.lab_to_sd(lab_sample)
    
    assert sd is not None
    assert hasattr(sd, 'wavelengths')
    assert hasattr(sd, 'values')

def test_ai_analysis_spc(ai_analysis):
    """Тест за Statistical Process Control."""
    historical_de = [0.5, 0.6, 0.4, 0.7, 0.5, 0.8, 0.4, 0.6, 0.5, 0.7]
    
    spc_data = ai_analysis.calculate_spc(historical_de)
    
    assert spc_data is not None
    assert "mean" in spc_data
    assert "ucl" in spc_data
    assert "lcl" in spc_data
    assert "status" in spc_data
    assert spc_data["ucl"] > spc_data["mean"]
    assert spc_data["lcl"] < spc_data["mean"]

def test_ai_analysis_trend_prediction(ai_analysis):
    """Тест за прогнозиране на тренд."""
    historical_de = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    trend_result = ai_analysis.predict_trend(historical_de)
    
    assert trend_result is not None
    assert "prediction" in trend_result
    assert "trend" in trend_result
    assert "slope" in trend_result

def test_ai_analysis_anomaly_detection(ai_analysis):
    """Тест за откриване на аномалии."""
    data_points = [0.5, 0.6, 0.4, 0.7, 2.5, 0.5, 0.6, 0.4]
    
    anomalies = ai_analysis.detect_anomalies(data_points)
    
    assert isinstance(anomalies, list)
    # The high value (2.5) should be detected as an anomaly
    assert len(anomalies) > 0

def test_ai_analysis_recipe_formulation(ai_analysis):
    """Тест за изчисляване на рецепта."""
    target_lab = [50.0, 10.0, 20.0]
    pigment_db = [
        {"name": "Titanium White", "lab": [98, 0, 0]},
        {"name": "Carbon Black", "lab": [5, 0, 0]},
        {"name": "Iron Oxide Red", "lab": [40, 30, 20]},
    ]
    
    result = ai_analysis.recipe_formulation(target_lab, pigment_db)
    
    assert result is not None
    assert "recommended_pigment" in result
    assert "estimated_delta_e" in result
    assert "concentration" in result

def test_ai_analysis_sustainability_index(ai_analysis):
    """Тест за изчисляване на sustainability index."""
    recipe_data = {
        "delta_e": 0.8,
        "components": [
            {"name": "Titanium White", "amount": 5.0},
            {"name": "Organic Pigment", "amount": 1.0}
        ]
    }
    batch_size = 100.0
    energy_data = 5.5
    
    sustainability = ai_analysis.calculate_sustainability_index(recipe_data, batch_size, energy_data)
    
    assert sustainability is not None
    assert "sustainability_score" in sustainability
    assert "co2_footprint_kg" in sustainability
    assert 0 <= sustainability["sustainability_score"] <= 100
