"""
Fringe rates by country and calendar year, 2022-2026, built from public sources.

Fringe = what an employer pays on top of base salary, as a share of base salary.
Arcadia's definition has four components, each sourced separately:

  1. social_contribution_rate   statutory employer social security and payroll taxes
  2. retirement_severance_rate  mandatory pension, provident, severance or gratuity
                                funding that sits outside social security
  3. statutory_pay_rate         pay the law adds beyond 12 monthly salaries
                                (13th salary, Christmas bonus, vacation premium)
  4. employer_benefits_rate     employer-provided health and retirement benefits;
                                United States only, where they replace public systems

Voluntary benefits outside the US (private medical, top-up pensions, meal vouchers)
are a company choice rather than a country cost, so they are left out. Rates change
on 1 January; the year is the calendar year.

Method by country
-----------------
* OECD members: employer social security contributions (including payroll taxes) for
  a single worker at 100% of the average wage, from OECD Taxing Wages Table 1.2,
  published as a share of labour costs and converted to a share of gross wages:
  rate = L / (100 - L). Each year comes from the edition that first reported it
  (2023 edition for 2022 ... 2026 edition for 2025).
* 2026 for OECD members: the 2027 edition is not out yet, so 2025 is carried forward
  and flagged is_estimate, except where a 2026 statutory change was confirmed
  (Germany, Spain, Ireland, Korea), which is added to the 2025 rate.
* United States: BLS Employer Costs for Employee Compensation (ECEC), private
  industry, management, professional and related occupations, March of each year.
  Base salary covers wages and paid leave, so every component is divided by
  (wages and salaries + paid leave).
* Countries with contribution ceilings (UK pension band, Switzerland BVG, Singapore
  CPF, Philippines SSS/PhilHealth/Pag-IBIG, South Africa UIF, India EDLI) are
  evaluated at a reference salary: Arcadia's L4 (Lead) base in that country.
* Brazil, India, UAE, South Africa, Singapore, Philippines: statutory rates from
  the sources listed in SOURCES.

Run this module directly to print the table.
"""

from __future__ import annotations

import datetime as dt

import fx_rates
import reference_data as ref

YEARS = [2022, 2023, 2024, 2025, 2026]

# --------------------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------------------
SOURCES = {
    "OECD-TW23": ("OECD, Taxing Wages 2023, Table 1.2 (2022 data)",
                  "https://www.oecd.org/en/publications/taxing-wages-2023_8c99fa4d-en/full-report/component-4.html"),
    "OECD-TW24": ("OECD, Taxing Wages 2024, Table 1.2 (2023 data)",
                  "https://www.oecd.org/en/publications/taxing-wages-2024_dbcbac85-en/full-report/component-4.html"),
    "OECD-TW25": ("OECD, Taxing Wages 2025, Table 1.2 (2024 data)",
                  "https://www.oecd.org/en/publications/taxing-wages-2025_b3a95829-en/full-report/overview_715add19.html"),
    "OECD-TW26": ("OECD, Taxing Wages 2026, Table 1.2 (2025 data)",
                  "https://www.oecd.org/en/publications/taxing-wages-2026_3a5169ef-en/full-report/overview_d93131c3.html"),
    "BLS-2022": ("BLS, Employer Costs for Employee Compensation, March 2022, Table 4",
                 "https://www.bls.gov/news.release/archives/ecec_06162022.pdf"),
    "BLS-2023": ("BLS, Employer Costs for Employee Compensation, March 2023, Table 4",
                 "https://www.bls.gov/news.release/archives/ecec_06162023.htm"),
    "BLS-2024": ("BLS, Employer Costs for Employee Compensation, March 2024, Table 4",
                 "https://www.bls.gov/news.release/archives/ecec_06182024.pdf"),
    "BLS-2025": ("BLS, Employer Costs for Employee Compensation, March 2025, Table 4",
                 "https://www.bls.gov/news.release/archives/ecec_06132025.htm"),
    "BLS-2026": ("BLS, Employer Costs for Employee Compensation, March 2026, Table 4",
                 "https://www.bls.gov/news.release/archives/ecec_06122026.htm"),
    "BR-STAT": ("Brazil employer payroll charges: INSS 20%, RAT, third parties ~5.8%, FGTS 8%, 13th salary, 1/3 vacation bonus",
                "https://www.globalexpansion.com/countrypedia/Brazil"),
    "MX-VAC": ("Mexico vacation reform (12 days from 1 Jan 2023), 25% vacation premium",
               "https://global.lockton.com/us/en/news-insights/mexico-to-increase-paid-vacation-days-for-all-employees"),
    "MX-LFT": ("Mexico Federal Labor Law art. 87: year-end bonus (aguinaldo) of at least 15 days' pay",
               "https://www.diputados.gob.mx/LeyesBiblio/pdf/LFT.pdf"),
    "DE-2026": ("German social insurance rates 2026 (average additional health contribution 2.9%)",
                "https://lohn-info.de/sozialversicherungsbeitraege2026.html"),
    "ES-MEI": ("Spain intergenerational equity mechanism (MEI) schedule 2023-2029",
               "https://institutosantalucia.es/actualidad/seguridad-social/mei-que-es-y-como-afecta-a-tu-nomina/"),
    "IE-2026": ("Ireland employer PRSI changes and My Future Fund auto-enrolment from 1 Jan 2026",
                "https://brightsg.com/blog/my-future-fund-prsi-budget-2026/"),
    "IE-PRSI": ("Ireland employer PRSI 11.25% from October 2025",
                "https://payroll.org/news-resources/news/news-detail/2026/01/05/ireland-s-budget-2026-brings-significant-changes-for-payroll"),
    "KR-2026": ("Korea 2026 national pension 9.5% (employer 4.75%) and health insurance 7.19%",
                "https://www.crowe.com/kr/en-us/news/news20260101_en"),
    "KR-SEV": ("Korea Employee Retirement Benefit Security Act: severance of 30 days' average wage per year of service",
               "https://www.atlashxm.com/resources/employee-benefits-in-south-korea"),
    "UK-AE": ("UK workplace pension auto-enrolment: employer minimum 3% of qualifying earnings (GBP 6,240-50,270)",
              "https://www.gov.uk/workplace-pensions/what-you-your-employer-and-the-government-pay"),
    "UK-LEVY": ("UK Apprenticeship Levy: 0.5% of pay bill above GBP 3 million",
                "https://www.gov.uk/guidance/pay-apprenticeship-levy"),
    "CH-BVG-22": ("Swiss BVG key figures 2022-2023 (coordination deduction, upper limit)", "https://finpension.ch/?p=8671"),
    "CH-BVG-25": ("Swiss BVG key figures 2025-2026 (coordination deduction, upper limit)",
                  "https://www.allianz.ch/content/dam/onemarketing/azch/common/allianz/en/bvg/allianz-api-key-opi-figures-interest-conversion-rates.pdf"),
    "AU-SG": ("Australia superannuation guarantee rate schedule (10.5% Jul 2022 ... 12% Jul 2025)",
              "https://australiansuper.com/superannuation/superannuation-articles/2024/07/understanding-the-superannuation-guarantee"),
    "AE-EOSG": ("UAE Federal Decree-Law 33/2021: end-of-service gratuity of 21 days' basic wage per year (first 5 years)",
                "https://www.morganlewis.com/pubs/2021/12/united-arab-emirates-updates-federal-labour-law"),
    "ZA-PWC": ("PwC Worldwide Tax Summaries, South Africa: UIF 1% (cap ZAR 177.12/month), SDL 1%",
               "https://taxsummaries.pwc.com/south-africa/corporate/other-taxes"),
    "IN-CODES": ("India labour codes in force 21 Nov 2025: wages at least 50% of remuneration for PF and gratuity",
                 "https://www.littler.com/news-analysis/asap/indias-labor-law-overhaul-snapshot-key-changes"),
    "IN-EPF": ("India Employees' Provident Funds Act 1952 (employer 12%; EDLI 0.5% and admin 0.5% on wages up to INR 15,000/month) and Payment of Gratuity Act 1972 (15/26 of monthly wage per year)",
               "https://www.epfindia.gov.in/"),
    "SG-CPF": ("CPF Board: monthly salary ceiling SGD 6,000 to 8,000 (2023-2026); employer rate 17% up to age 55",
               "https://cpf.gov.sg/member/infohub/news/media-news/budget-2023-cpf-monthly-salary-ceiling-to-be-raised-to-8000-by-2026"),
    "SG-SDL": ("GoBusiness Singapore: Skills Development Levy 0.25% of monthly pay, maximum SGD 11.25 per employee",
               "https://gobusiness.gov.sg/about-skills-development-levy"),
    "PH-SSS23": ("Philippines SSS schedule 2023 (14%, employer 9.5%, MSC cap PHP 30,000) vs 2021-2022 (13%, employer 8.5%, cap PHP 25,000)",
                 "https://forvismazars.com/ph/en/insights/hr-payroll-alerts/new-sss-contribution-rates-for-2023"),
    "PH-PWC": ("PwC Worldwide Tax Summaries, Philippines: SSS 15% from 2025 (cap PHP 35,000), PhilHealth 5% (ceiling PHP 100,000) from 2024, Pag-IBIG PHP 200 from Feb 2024",
               "https://taxsummaries.pwc.com/philippines/individual"),
    "PH-13M": ("Philippines Presidential Decree 851: mandatory 13th month pay (1/12 of annual basic salary)",
               "https://www.dole.gov.ph/"),
}

# --------------------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------------------
# OECD Taxing Wages, employer SSC incl. payroll taxes, % of labour costs, 100% average wage
OECD_EMPLOYER_SSC = {
    #      2022   2023   2024   2025
    "US": (7.5,   7.5,   7.5,   7.5),
    "CA": (8.4,   8.4,   8.7,   8.8),
    "MX": (10.3,  10.1,  9.9,   9.8),
    "GB": (10.4,  10.1,  10.2,  12.0),
    "IE": (10.0,  10.0,  10.0,  10.1),
    "DE": (16.6,  16.7,  16.8,  17.3),
    "FR": (26.7,  26.6,  26.7,  26.7),
    "NL": (10.7,  10.7,  10.8,  11.2),
    "ES": (23.0,  23.3,  23.4,  23.4),
    "PT": (19.2,  19.2,  19.2,  19.2),
    "PL": (14.1,  14.1,  14.1,  14.0),
    "CH": (6.0,   6.0,   6.0,   6.0),
    "SE": (23.9,  23.9,  23.9,  23.9),
    "JP": (13.3,  13.5,  13.6,  13.5),
    "AU": (5.1,   5.7,   5.7,   5.7),
    "KR": (9.9,   10.0,  10.0,  10.0),
}
OECD_SOURCE_BY_YEAR = {2022: "OECD-TW23", 2023: "OECD-TW24", 2024: "OECD-TW25", 2025: "OECD-TW26"}

# Confirmed 2026 statutory changes, in percentage points of gross wages (employer side)
OECD_2026_ADJUSTMENT_PP = {
    "DE": (0.20,  "DE-2026", "Average additional health contribution 2.5% -> 2.9%, employer pays half"),
    "ES": (0.08,  "ES-MEI",  "MEI employer share 0.67% -> 0.75%"),
    "IE": (0.1125, "IE-PRSI", "Employer PRSI 11.25% all year plus 11.40% from Oct 2026, vs 2025 average"),
    "KR": (0.31,  "KR-2026", "Pension employer 4.5% -> 4.75%, health 3.545% -> 3.595%, long-term care"),
}

# BLS ECEC, private industry, management/professional/related, $ per hour worked (March)
BLS_ECEC = {
    #       wages  paid_leave  insurance  retirement  legally_required
    2022: (44.92, 6.09, 4.60, 2.43, 4.26),
    2023: (47.55, 6.45, 4.76, 2.53, 4.51),
    2024: (50.24, 6.86, 5.00, 2.79, 4.72),
    2025: (52.15, 7.11, 5.26, 2.89, 4.86),
    2026: (53.50, 7.34, 5.73, 2.89, 5.03),
}

AU_SUPER_GUARANTEE_CALENDAR = {   # July changes averaged over each calendar year
    2022: (0.100 + 0.105) / 2, 2023: (0.105 + 0.110) / 2, 2024: (0.110 + 0.115) / 2,
    2025: (0.115 + 0.120) / 2, 2026: 0.120,
}
CH_BVG = {   # coordination deduction, upper limit (CHF/year); 2024 = 2023, adjusted every two years
    2022: (25_095, 86_040), 2023: (25_725, 88_200), 2024: (25_725, 88_200),
    2025: (26_460, 90_720), 2026: (26_460, 90_720),
}
CH_BVG_EMPLOYER_SHARE_OF_COORDINATED = 0.05   # 10% age credit (age 35-44), employer pays half
SG_CPF_MONTHLY_CEILING = {2022: 6000, 2023: (8 * 6000 + 4 * 6300) / 12, 2024: 6800, 2025: 7400, 2026: 8000}
PH_MONTHLY_EMPLOYER = {   # SSS incl. EC (PHP 30), PhilHealth employer half, Pag-IBIG
    2022: 0.085 * 25_000 + 30 + 0.04 / 2 * 80_000 + 100,
    2023: 0.095 * 30_000 + 30 + 0.04 / 2 * 80_000 + 100,
    2024: 0.095 * 30_000 + 30 + 0.05 / 2 * 100_000 + (100 + 11 * 200) / 12,
    2025: 0.100 * 35_000 + 30 + 0.05 / 2 * 100_000 + 200,
    2026: 0.100 * 35_000 + 30 + 0.05 / 2 * 100_000 + 200,
}
ARCADIA_BASIC_SHARE = {"IN": 0.50, "AE": 0.60}   # Arcadia pay policy: basic wage within base salary


def reference_salary(cc: str) -> float:
    """Arcadia's L4 (Lead) annual base in local currency: the salary ceilings are tested at."""
    _, _, cur, pay_index, _ = ref.COUNTRIES[cc]
    fx = fx_rates.usd_per_local(cur, dt.date.fromisoformat(ref.LEVEL_BASE_FX_DATE))
    return round(ref.JOB_LEVELS[4][3] * pay_index / fx, -2)


def _gross(labour_cost_pct: float) -> float:
    return labour_cost_pct / (100.0 - labour_cost_pct)


def build() -> tuple[list[dict], list[dict]]:
    rows, cites = [], []

    def cite(cc, year, component, key):
        cites.append({"country_code": cc, "year": year, "component": component,
                      "source_id": key, "source_title": SOURCES[key][0], "source_url": SOURCES[key][1]})

    for cc in ref.COUNTRIES:
        ref_salary = reference_salary(cc)
        for year in YEARS:
            social = retire = stat_pay = benefits = 0.0
            estimate, notes = False, []

            # 1. employer social security (OECD members except the US)
            if cc in OECD_EMPLOYER_SSC and cc != "US":
                if year <= 2025:
                    social = _gross(OECD_EMPLOYER_SSC[cc][year - 2022])
                    cite(cc, year, "social_contribution_rate", OECD_SOURCE_BY_YEAR[year])
                else:
                    social = _gross(OECD_EMPLOYER_SSC[cc][3])
                    cite(cc, year, "social_contribution_rate", "OECD-TW26")
                    if cc in OECD_2026_ADJUSTMENT_PP:
                        pp, key, why = OECD_2026_ADJUSTMENT_PP[cc]
                        social += pp / 100
                        cite(cc, year, "social_contribution_rate", key)
                        notes.append(f"2025 OECD rate + {pp:.2f} pp: {why}")
                    else:
                        estimate = True
                        notes.append("2025 OECD rate carried forward (2026 data not yet published)")

            if cc == "US":
                w, pl, ins, ret, lr = BLS_ECEC[year]
                social, benefits = lr / (w + pl), (ins + ret) / (w + pl)
                cite(cc, year, "social_contribution_rate", f"BLS-{year}")
                cite(cc, year, "employer_benefits_rate", f"BLS-{year}")
                notes.append("BLS ECEC: legally required + (insurance + retirement), over wages + paid leave")

            elif cc == "BR":
                extra_months = 1 + 1 / 3            # 13th salary + one-third vacation bonus
                pay_factor = (12 + extra_months) / 12
                social = (0.20 + 0.02 + 0.058) * pay_factor   # INSS + RAT (2%, FAP 1.0) + third parties
                retire = 0.08 * pay_factor                     # FGTS
                stat_pay = extra_months / 12
                for comp in ("social_contribution_rate", "retirement_severance_rate", "statutory_pay_rate"):
                    cite(cc, year, comp, "BR-STAT")
                notes.append("Standard payroll regime (not Simples Nacional or CPRB); charges also due on 13th and vacation bonus")

            elif cc == "MX":
                vacation_days = 6 if year == 2022 else 12
                stat_pay = 15 / 365 + 0.25 * vacation_days / 365
                cite(cc, year, "statutory_pay_rate", "MX-LFT")
                cite(cc, year, "statutory_pay_rate", "MX-VAC")
                notes.append(f"Aguinaldo 15 days + 25% premium on {vacation_days} vacation days")

            elif cc == "GB":
                social += 0.005
                retire = 0.03 * (min(ref_salary, 50_270) - 6_240) / ref_salary
                cite(cc, year, "social_contribution_rate", "UK-LEVY")
                cite(cc, year, "retirement_severance_rate", "UK-AE")

            elif cc == "IE" and year >= 2026:
                retire = 0.015
                cite(cc, year, "retirement_severance_rate", "IE-2026")
                notes.append("Auto-enrolment employer 1.5% from 1 Jan 2026 (applied to full base)")

            elif cc == "CH":
                deduction, upper = CH_BVG[year]
                coordinated = max(0.0, min(ref_salary, upper) - deduction)
                retire = CH_BVG_EMPLOYER_SHARE_OF_COORDINATED * coordinated / ref_salary
                cite(cc, year, "retirement_severance_rate", "CH-BVG-22" if year <= 2024 else "CH-BVG-25")
                notes.append("BVG mandatory minimum: employer half of the 10% age credit on coordinated salary")

            elif cc == "KR":
                retire = 1 / 12
                cite(cc, year, "retirement_severance_rate", "KR-SEV")

            elif cc == "AU":
                retire = AU_SUPER_GUARANTEE_CALENDAR[year]
                cite(cc, year, "retirement_severance_rate", "AU-SG")

            elif cc == "AE":
                retire = 21 / 365 * ARCADIA_BASIC_SHARE["AE"]
                cite(cc, year, "retirement_severance_rate", "AE-EOSG")
                notes.append("Expatriate staff: no GPSSA; gratuity on basic wage = 60% of base (Arcadia policy)")

            elif cc == "ZA":
                social = 0.01 + min(0.01 * ref_salary, 177.12 * 12) / ref_salary
                cite(cc, year, "social_contribution_rate", "ZA-PWC")

            elif cc == "IN":
                basic = ARCADIA_BASIC_SHARE["IN"]
                retire = basic * (0.12 + (15 / 26) / 12) + 0.01 * 15_000 * 12 / ref_salary
                cite(cc, year, "retirement_severance_rate", "IN-EPF")
                cite(cc, year, "retirement_severance_rate", "IN-CODES")
                notes.append("PF 12% and gratuity 4.81% on basic = 50% of base (meets the labour codes' 50% wage rule)")

            elif cc == "SG":
                retire = 0.17 * SG_CPF_MONTHLY_CEILING[year] * 12 / ref_salary
                social = min(0.0025 * ref_salary / 12, 11.25) * 12 / ref_salary
                cite(cc, year, "retirement_severance_rate", "SG-CPF")
                cite(cc, year, "social_contribution_rate", "SG-SDL")
                notes.append("CPF on ordinary wages up to the monthly ceiling; citizens and PRs")

            elif cc == "PH":
                social = PH_MONTHLY_EMPLOYER[year] * 12 / ref_salary
                stat_pay = 1 / 12
                cite(cc, year, "social_contribution_rate", "PH-SSS23" if year <= 2023 else "PH-PWC")
                cite(cc, year, "statutory_pay_rate", "PH-13M")

            total = social + retire + stat_pay + benefits
            rows.append({
                "country_code": cc, "year": year,
                "effective_start_date": dt.date(year, 1, 1), "effective_end_date": dt.date(year, 12, 31),
                "social_contribution_rate": round(social, 4),
                "retirement_severance_rate": round(retire, 4),
                "statutory_pay_rate": round(stat_pay, 4),
                "employer_benefits_rate": round(benefits, 4),
                "fringe_rate": round(round(social, 4) + round(retire, 4) + round(stat_pay, 4) + round(benefits, 4), 4),
                "reference_salary_local": ref_salary,
                "is_estimate": estimate,
                "method_note": "; ".join(notes),
            })
    return rows, cites


if __name__ == "__main__":
    import pandas as pd
    table, _ = build()
    df = pd.DataFrame(table).pivot(index="country_code", columns="year", values="fringe_rate")
    print((df * 100).round(1).to_string())
