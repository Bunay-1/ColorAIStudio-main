from typing import List, Dict, Tuple, Optional, Any, Union
import numpy as np
import colour
from colour.difference import delta_E_CIE1976, delta_E_CIE1994, delta_E_CIE2000, delta_E_CMC

class ColorEngine:
    def __init__(self) -> None:
        # Поддържани наблюдатели
        self.observers = {
            "CIE 1931 2 Degree": "CIE 1931 2 Degree Standard Observer",
            "CIE 1964 10 Degree": "CIE 1964 10 Degree Standard Observer",
            "CIE 2012 2 Degree": "CIE 2012 2 Degree Standard Observer",
            "CIE 2012 10 Degree": "CIE 2012 10 Degree Standard Observer"
        }

        # Поддържани илюминанти
        self.illuminants = [
            "D50", "D55", "D60", "D65", "D75",
            "A", "C",
            "F1", "F2", "F3", "F4", "F5", "F6",
            "F7", "F8", "F9", "F10", "F11", "F12",
            "LED-B1", "LED-B2", "LED-B3", "LED-B4", "LED-B5",
            "LED-BH1", "LED-RGB1", "LED-V1", "LED-V2"
        ]

        # Базова RAL Classic таблица (Lab координати под D65/2)
        self.ral_table = {
            "RAL 1018": {"name": "Zinc yellow", "lab": [81.54, -0.63, 71.49]},
            "RAL 3020": {"name": "Traffic red", "lab": [42.14, 59.95, 33.15]},
            "RAL 5002": {"name": "Ultramarine blue", "lab": [23.10, 8.44, -45.54]},
            "RAL 6018": {"name": "Yellow green", "lab": [56.33, -37.78, 44.59]},
            "RAL 7035": {"name": "Light grey", "lab": [75.69, -1.04, 1.48]},
            "RAL 9003": {"name": "Signal white", "lab": [93.18, -0.92, 0.44]},
            "RAL 9005": {"name": "Jet black", "lab": [5.00, 0.00, 0.00]},
            "RAL 9010": {"name": "Pure white", "lab": [94.57, -1.06, 2.76]}
        }

    def get_closest_ral(self, lab: List[float]) -> Optional[Dict[str, Union[str, float]]]:
        """Намира най-близкия RAL цвят по Delta E 2000."""
        best_match: Optional[Dict[str, Union[str, float]]] = None
        min_de: float = 999.0

        for code, data in self.ral_table.items():
            de: float = delta_E_CIE2000(lab, data["lab"])
            if de < min_de:
                min_de = de
                best_match = {"code": code, "name": data["name"], "delta_e": float(de)}

        return best_match

    def calculate_delta_e(self, lab1: List[float], lab2: List[float], method: str = "CIE2000") -> float:
        """Пресмята разликата между два цвята."""
        if method == "CIE76":
            return float(delta_E_CIE1976(lab1, lab2))
        elif method == "CIE94":
            return float(delta_E_CIE1994(lab1, lab2))
        elif method == "CIE2000":
            return float(delta_E_CIE2000(lab1, lab2))
        elif method == "CMC":
            return float(delta_E_CMC(lab1, lab2))
        return float(delta_E_CIE2000(lab1, lab2))

    def get_chromaticity_coords(self, lab: List[float], illuminant: str = "D65", observer: str = "CIE 1931 2 Degree") -> Dict[str, float]:
        """Връща координати за диаграми (xy) базирано на Lab, илюминант и наблюдател."""
        illuminant_name: str = illuminant if illuminant in colour.CCS_ILLUMINANTS[observer] else "D65"
        white_point = colour.CCS_ILLUMINANTS[observer][illuminant_name]
        xyz = colour.Lab_to_XYZ(lab, white_point)
        xy = colour.XYZ_to_xy(xyz)
        return {"x": float(xy[0]), "y": float(xy[1])}

    def get_whiteness_yellowness(self, lab: List[float], illuminant: str = "D65", observer: str = "CIE 1931 2 Degree") -> Dict[str, float]:
        white_point = colour.CCS_ILLUMINANTS[observer][illuminant]
        xyz = colour.Lab_to_XYZ(lab, white_point)
        w_cie = colour.whiteness_CIE1982(xyz, white_point)
        y_astm = colour.yellowness_ASTM_E313_00(xyz)
        return {"whiteness_cie": float(w_cie[0]), "yellowness_astm": float(y_astm)}

    def calculate_mi(self, sd_sample, sd_standard):
        """
        Metamerism Index (MI).
        Изчислява MI под D65, A и FL11. Предупреждава ако MI > 0.5.
        """
        # Осигуряваме съвместимост с ASTM E308 чрез интерполация до 10nm стъпка
        sd_sample = sd_sample.copy().interpolate(colour.SpectralShape(400, 700, 10))
        sd_standard = sd_standard.copy().interpolate(colour.SpectralShape(400, 700, 10))

        illuminants = ["D65", "A", "FL11"]
        cmfs = colour.MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]

        results = {}
        max_mi = 0
        for ill_name in illuminants:
            ill_sd = colour.SDS_ILLUMINANTS[ill_name]
            # Използваме integration метода за избягване на ASTM E308 ограничения
            xyz1 = colour.sd_to_XYZ(sd_sample, cmfs, ill_sd, method='Integration')
            xyz2 = colour.sd_to_XYZ(sd_standard, cmfs, ill_sd, method='Integration')
            lab1 = colour.XYZ_to_Lab(xyz1 / 100)
            lab2 = colour.XYZ_to_Lab(xyz2 / 100)
            de = delta_E_CIE2000(lab1, lab2)
            results[ill_name] = float(de)
            max_mi = max(max_mi, de)

        return {
            "mi_values": results,
            "warning": bool(max_mi > 0.5),
            "max_mi": float(max_mi),
            "status": "Критичен метамеризъм!" if max_mi > 0.5 else "Стабилен цвят"
        }

    def interpolate_spectrum(self, wavelengths: List[float], values: List[float], target_step: int = 1) -> Tuple[List[float], List[float]]:
        """Интерполира спектрални данни до 1nm стъпка."""
        from scipy.interpolate import interp1d
        f = interp1d(wavelengths, values, kind='cubic')
        new_wavelengths = np.arange(min(wavelengths), max(wavelengths) + 1, target_step)
        new_values = f(new_wavelengths)
        return new_wavelengths.tolist(), new_values.tolist()

    def get_color_description(self, lab: List[float]) -> str:
        """Генерира автоматично текстово описание на цвета за RAG."""
        L, a, b = lab
        desc: str = ""

        # Интеграция на RAL в описанието
        closest_ral = self.get_closest_ral(lab)
        if closest_ral and closest_ral["delta_e"] < 5.0:
            desc += f"цвят близък до {closest_ral['code']} ({closest_ral['name']}), "

        if L > 70:
            desc += "светъл "
        elif L < 30:
            desc += "тъмен "

        if abs(a) > abs(b):
            desc += "червеникав " if a > 0 else "зеленикав "
        else:
            desc += "жълтеникав " if b > 0 else "синкав "

        return desc.strip().rstrip(",")

    def analyze_hsi_cube(self, hsi_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализира хиперспектрален куб (HSI Cube).
        hsi_data: речник с 'wavelengths' и 'intensity_matrix' (x, y, lambda)
        """
        wavelengths = hsi_data.get("wavelengths")
        matrix = np.array(hsi_data.get("intensity_matrix"))

        # 1. Изчисляване на среден спектър
        mean_spectrum = np.mean(matrix, axis=(0, 1))

        # 2. Детекция на химически пикове (примерни за индустриални полимери)
        # Напр. 1720nm е типичен за карбонилни групи (оксидация на полимери)
        chemical_markers = {
            "Polystyrene": 1680,
            "Polyethylene": 1730,
            "Polypropylene": 1710,
            "Surface Oxidation": 1720
        }

        detected_materials = []
        for material, peak in chemical_markers.items():
            # Намиране на най-близката дължина на вълната
            idx = (np.abs(np.array(wavelengths) - peak)).argmin()
            if mean_spectrum[idx] > 0.4: # Демо праг за детекция
                detected_materials.append(material)

        return {
            "mean_spectrum": mean_spectrum.tolist(),
            "detected_materials": detected_materials,
            "purity_index": float(np.max(mean_spectrum) - np.min(mean_spectrum))
        }

    def detect_subsurface_defect(self, spectral_reflectance: List[float]) -> Dict[str, Union[bool, str, float]]:
        """
        Открива дефекти под повърхността (напр. корозия под боя).
        Използва NIR (Near-Infrared) сигнатури.
        """
        # Спектрална сигнатура на корозия обикновено е в 750-950nm
        # Симулираме проверка
        is_defect: bool = False
        if len(spectral_reflectance) > 50:  # Трябва ни широк спектър
            # Проверка за специфичен спад в NIR
            nir_region = spectral_reflectance[40:60]  # Демонстрационен регион
            if np.std(nir_region) > 0.15:
                is_defect = True

        return {
            "subsurface_defect": is_defect,
            "type": "Corrosion/Delamination" if is_defect else "None",
            "confidence": 0.85 if is_defect else 0.98
        }

if __name__ == "__main__":
    engine = ColorEngine()
    print("Color Engine updated with full illuminant support.")
