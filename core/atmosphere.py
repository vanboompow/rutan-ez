"""ISA Standard Atmosphere Model (Troposphere).

Reference: Anderson, Introduction to Flight, Ch. 3.

Provides density, pressure, temperature, and viscosity as functions
of altitude for use in Reynolds number calculation and flutter analysis.

Valid for altitudes 0 to 36,089 ft (troposphere only). Inputs above
the tropopause are clamped to 36,089 ft.
"""

import math


# ISA sea-level constants
_T0 = 518.67  # Rankine (59 F)
_P0 = 2116.22  # lb/ft^2
_RHO0 = 0.002377  # slug/ft^3
_LAPSE_RATE = 0.003566  # R/ft (temperature lapse rate)
_TROPOPAUSE_FT = 36089.0  # Troposphere ceiling

# Sutherland's law constants for air
_MU_REF = 3.737e-7  # Reference viscosity coefficient
_S_CONST = 198.72  # Sutherland constant (Rankine)


def _clamp_altitude(altitude_ft: float) -> float:
    """Clamp altitude to troposphere (0 to 36,089 ft)."""
    return max(0.0, min(altitude_ft, _TROPOPAUSE_FT))


def temperature(altitude_ft: float) -> float:
    """ISA temperature in Rankine."""
    return _T0 - _LAPSE_RATE * _clamp_altitude(altitude_ft)


def pressure(altitude_ft: float) -> float:
    """ISA pressure in lb/ft^2."""
    t_ratio = temperature(altitude_ft) / _T0
    return _P0 * t_ratio**5.2561


def density(altitude_ft: float) -> float:
    """ISA air density in slug/ft^3."""
    t_ratio = temperature(altitude_ft) / _T0
    return _RHO0 * t_ratio**4.2561


def viscosity(altitude_ft: float) -> float:
    """Dynamic viscosity via Sutherland's law in slug/(ft*s)."""
    t = temperature(altitude_ft)
    return _MU_REF * (t / _T0) ** 1.5 * (_T0 + _S_CONST) / (t + _S_CONST)


def speed_of_sound(altitude_ft: float) -> float:
    """Speed of sound in ft/s.  a = sqrt(gamma * R * T)."""
    gamma = 1.4
    R_air = 1716.49  # ft*lb/(slug*R)
    return math.sqrt(gamma * R_air * temperature(altitude_ft))
