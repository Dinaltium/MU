"""
models/pkpd_model.py

WHY ONE-COMPARTMENT PK MODEL:
  The one-compartment model is the accepted standard for clinical
  dose calculations in primary care. It accurately predicts:
    - Peak serum concentration (C_max)
    - Average steady-state concentration (C_avg)
    - How renal impairment extends half-life (requiring dose adjustment)

  More complex two/three-compartment models add precision but require
  clinical pharmacokinetic studies per drug — impractical at the
  formulary scale of a hackathon. For the diseases and drugs we target
  (community-acquired infections), the one-compartment model is
  clinically defensible.

SECURITY NOTE:
  • PK_PARAMS is a hardcoded dict from published pharmacokinetic studies,
    not from user input. A malicious actor cannot inflate drug
    concentrations by manipulating the request.
  • Division by Vd is guarded against zero: Vd = Vd_per_kg * weight,
    and weight is validated as positive in the patients table (DB CHECK).
  • renal_function of 0 would cause division by zero in t_half calculation;
    we clamp it to a minimum of 0.1 (severe impairment).
"""

import math
import logging

logger = logging.getLogger(__name__)

# Sources: standard pharmacokinetic references (Brunton et al., Goodman & Gilman)
PK_PARAMS: dict[str, dict] = {
    "amoxicillin": {
        "bioavailability":       0.90,
        "volume_distribution":   0.26,   # L/kg
        "half_life_hours":       1.3,
        "standard_dose_mg":      500,
        "dosing_interval_hours": 8,
    },
    "azithromycin": {
        "bioavailability":       0.37,
        "volume_distribution":   31.1,
        "half_life_hours":       68,
        "standard_dose_mg":      500,
        "dosing_interval_hours": 24,
    },
    "ciprofloxacin": {
        "bioavailability":       0.70,
        "volume_distribution":   2.5,
        "half_life_hours":       4,
        "standard_dose_mg":      500,
        "dosing_interval_hours": 12,
    },
    "doxycycline": {
        "bioavailability":       0.93,
        "volume_distribution":   0.75,
        "half_life_hours":       18,
        "standard_dose_mg":      100,
        "dosing_interval_hours": 12,
    },
    "metronidazole": {
        "bioavailability":       1.00,
        "volume_distribution":   0.85,
        "half_life_hours":       8,
        "standard_dose_mg":      400,
        "dosing_interval_hours": 8,
    },
    "chloroquine": {
        "bioavailability":       0.89,
        "volume_distribution":   250,
        "half_life_hours":       240,    # 10 days — accumulates
        "standard_dose_mg":      250,
        "dosing_interval_hours": 24,
    },
}


class PKPDModel:
    def calculate_concentration(
        self,
        drug: str,
        weight: float,
        renal_function: float = 1.0,
    ) -> float:
        """
        Calculate average steady-state drug concentration (C_avg, mg/L).

        renal_function: 0.0 (ESRD) → 1.0 (normal GFR)
        Returns 1.0 (neutral ratio) if drug is unknown.
        """
        params = PK_PARAMS.get(drug.lower())
        if not params:
            logger.debug("No PK params for drug '%s' — returning 1.0", drug)
            return 1.0

        weight         = max(weight, 1.0)           # avoid zero-weight
        renal_function = max(renal_function, 0.1)   # avoid zero-division (ESRD floor)

        dose = params["standard_dose_mg"]
        F    = params["bioavailability"]
        Vd   = params["volume_distribution"] * weight          # total L
        t_half_adjusted = params["half_life_hours"] / renal_function
        tau  = params["dosing_interval_hours"]

        ke    = 0.693 / t_half_adjusted
        C_avg = (F * dose) / (Vd * ke * tau)

        return round(C_avg, 4)
