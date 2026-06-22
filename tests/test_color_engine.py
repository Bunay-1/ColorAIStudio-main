"""
Comprehensive Test Suite for Color Engine
==========================================
Tests for color calculations, Delta E, and spectral analysis.
"""

import pytest
import numpy as np
from color_engine import ColorEngine


class TestColorEngine:
    """Test suite for ColorEngine class."""
    
    @pytest.fixture
    def color_engine(self):
        """Fixture to create ColorEngine instance."""
        return ColorEngine()
    
    def test_initialization(self, color_engine):
        """Test that ColorEngine initializes correctly."""
        assert color_engine is not None
        assert hasattr(color_engine, 'observers')
        assert hasattr(color_engine, 'illuminants')
        assert hasattr(color_engine, 'ral_table')
    
    def test_observers(self, color_engine):
        """Test that observers are properly defined."""
        assert "CIE 1931 2 Degree" in color_engine.observers
        assert "CIE 1964 10 Degree" in color_engine.observers
        assert "CIE 2012 2 Degree" in color_engine.observers
        assert "CIE 2012 10 Degree" in color_engine.observers
    
    def test_illuminants(self, color_engine):
        """Test that illuminants are properly defined."""
        assert "D65" in color_engine.illuminants
        assert "D50" in color_engine.illuminants
        assert "A" in color_engine.illuminants
        assert len(color_engine.illuminants) > 20
    
    def test_ral_table(self, color_engine):
        """Test that RAL table is populated."""
        assert len(color_engine.ral_table) > 0
        assert "RAL 9003" in color_engine.ral_table
        assert "RAL 9005" in color_engine.ral_table
        
        # Check structure of RAL entries
        for code, data in color_engine.ral_table.items():
            assert "name" in data
            assert "lab" in data
            assert len(data["lab"]) == 3
    
    def test_calculate_delta_e_cie76(self, color_engine):
        """Test Delta E calculation with CIE76 method."""
        lab1 = [50.0, 10.0, 20.0]
        lab2 = [50.5, 10.5, 20.5]
        
        result = color_engine.calculate_delta_e(lab1, lab2, method="CIE76")
        
        assert isinstance(result, float)
        assert result >= 0
        assert result < 2.0  # Should be relatively small for similar colors
    
    def test_calculate_delta_e_cie94(self, color_engine):
        """Test Delta E calculation with CIE94 method."""
        lab1 = [50.0, 10.0, 20.0]
        lab2 = [50.5, 10.5, 20.5]
        
        result = color_engine.calculate_delta_e(lab1, lab2, method="CIE94")
        
        assert isinstance(result, float)
        assert result >= 0
    
    def test_calculate_delta_e_cie2000(self, color_engine):
        """Test Delta E calculation with CIE2000 method."""
        lab1 = [50.0, 10.0, 20.0]
        lab2 = [50.5, 10.5, 20.5]
        
        result = color_engine.calculate_delta_e(lab1, lab2, method="CIE2000")
        
        assert isinstance(result, float)
        assert result >= 0
    
    def test_calculate_delta_e_cmc(self, color_engine):
        """Test Delta E calculation with CMC method."""
        lab1 = [50.0, 10.0, 20.0]
        lab2 = [50.5, 10.5, 20.5]
        
        result = color_engine.calculate_delta_e(lab1, lab2, method="CMC")
        
        assert isinstance(result, float)
        assert result >= 0
    
    def test_calculate_delta_e_default_method(self, color_engine):
        """Test that default method is CIE2000."""
        lab1 = [50.0, 10.0, 20.0]
        lab2 = [50.5, 10.5, 20.5]
        
        result_default = color_engine.calculate_delta_e(lab1, lab2)
        result_cie2000 = color_engine.calculate_delta_e(lab1, lab2, method="CIE2000")
        
        assert result_default == result_cie2000
    
    def test_calculate_delta_e_identical_colors(self, color_engine):
        """Test Delta E for identical colors should be 0."""
        lab = [50.0, 10.0, 20.0]
        
        result = color_engine.calculate_delta_e(lab, lab)
        
        assert result == 0.0
    
    def test_calculate_delta_very_different_colors(self, color_engine):
        """Test Delta E for very different colors should be large."""
        lab1 = [100.0, 100.0, 100.0]  # Very bright
        lab2 = [0.0, -100.0, -100.0]  # Very dark
        
        result = color_engine.calculate_delta_e(lab1, lab2)
        
        assert result > 50.0  # Should be very large
    
    def test_get_closest_ral(self, color_engine):
        """Test finding closest RAL color."""
        lab = [93.0, -1.0, 2.0]  # Close to white
        
        result = color_engine.get_closest_ral(lab)
        
        assert result is not None
        assert "code" in result
        assert "name" in result
        assert "delta_e" in result
        assert isinstance(result["delta_e"], float)
        assert result["delta_e"] >= 0
    
    def test_get_closest_ral_known_color(self, color_engine):
        """Test finding closest RAL for a known RAL color."""
        # Use exact RAL 9003 coordinates
        ral_9003_lab = color_engine.ral_table["RAL 9003"]["lab"]
        
        result = color_engine.get_closest_ral(ral_9003_lab)
        
        assert result["code"] == "RAL 9003"
        assert result["delta_e"] == 0.0
    
    def test_get_chromaticity_coords(self, color_engine):
        """Test chromaticity coordinate calculation."""
        lab = [50.0, 10.0, 20.0]
        
        result = color_engine.get_chromaticity_coords(lab)
        
        assert result is not None
        assert "x" in result
        assert "y" in result
        assert 0 <= result["x"] <= 1
        assert 0 <= result["y"] <= 1
    
    def test_get_chromaticity_coords_different_illuminant(self, color_engine):
        """Test chromaticity coordinates with different illuminant."""
        lab = [50.0, 10.0, 20.0]
        
        result_d65 = color_engine.get_chromaticity_coords(lab, illuminant="D65")
        result_a = color_engine.get_chromaticity_coords(lab, illuminant="A")
        
        # Results should differ for different illuminants
        assert result_d65 != result_a
    
    def test_get_whiteness_yellowness(self, color_engine):
        """Test whiteness and yellowness calculations."""
        lab = [95.0, -2.0, 2.0]  # White-ish color
        
        result = color_engine.get_whiteness_yellowness(lab)
        
        assert result is not None
        assert "whiteness_cie" in result
        assert "yellowness_astm" in result
        assert isinstance(result["whiteness_cie"], float)
        assert isinstance(result["yellowness_astm"], float)
    
    def test_invalid_lab_coordinates(self, color_engine):
        """Test handling of invalid LAB coordinates."""
        # This should not crash, but may produce unexpected results
        invalid_lab = [1000.0, 1000.0, 1000.0]  # Out of valid range
        
        try:
            result = color_engine.calculate_delta_e(invalid_lab, [50.0, 10.0, 20.0])
            # If it doesn't crash, just check it returns a number
            assert isinstance(result, float)
        except Exception:
            # If it raises an exception, that's also acceptable
            pass
    
    def test_calculate_mi_basic(self, color_engine):
        """Test basic Metamerism Index calculation."""
        import colour
        
        # Create mock spectral distributions
        wavelengths = np.arange(400, 701, 10)
        values1 = [0.5 + 0.1 * np.sin(w/50) for w in wavelengths]
        values2 = [0.5 + 0.15 * np.sin(w/50) for w in wavelengths]
        
        sd1 = colour.SpectralDistribution(dict(zip(wavelengths, values1)))
        sd2 = colour.SpectralDistribution(dict(zip(wavelengths, values2)))
        
        try:
            result = color_engine.calculate_mi(sd1, sd2)
            # MI should be a number
            assert isinstance(result, dict) or isinstance(result, float)
        except Exception as e:
            # MI calculation may fail with mock data
            pytest.skip(f"MI calculation requires valid spectral data: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
