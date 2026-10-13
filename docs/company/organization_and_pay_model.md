# Organization and pay model

How Arcadia Systems is organized, how people are paid, and where the external numbers (FX and fringe) come from. Arcadia is fictional: the org design, pay structure, bonus plan and people are invented. The FX rates, fringe rates, postal codes and coordinates are real and sourced.

- [Organization](#organization)
- [Job levels and base salary](#job-levels-and-base-salary)
- [How pay moves](#how-pay-moves)
- [Performance rating and bonus](#performance-rating-and-bonus)
- [Offices](#offices)
- [Currency](#currency)
- [Fringe rates](#fringe-rates)

## Organization

```
CEO
└── 8 function heads (executive officers)
    ├── 4 sub-function heads (SVP) in Technology and Commercial
    │   └── department heads
    └── department heads (functions with a single sub-function)
        └── Senior Directors (L8) → Directors (L7) → Senior Managers / Managers (L6, L5) → teams
```

| Function | Leader | Sub-functions | Departments |
|---|---|---|---|
| Technology | Chief Technology Officer (L11) | Engineering, Infrastructure | Core Platform Engineering, Product Engineering, Mobile & Web Engineering, Analytics Engineering, Data & AI Platform (from Nov 2024), Site Reliability, Information Security, Enterprise IT |
| Commercial | Chief Revenue Officer (L11) | Sales, Client Services | Enterprise Sales Americas / EMEA / APAC, Sales Operations, Partnerships, Client Success, Technical Support |
| Operations | Chief Operating Officer (L11) | | Customer Operations, Trust & Safety Operations, Workplace & Procurement |
| Product | Chief Product Officer (L11) | | Product Management, Design & Research |
| Finance | Chief Financial Officer (L11) | | FP&A, Accounting & Controllership, Treasury & Tax |
| People | Chief People Officer (L10) | | HR Business Partners, Talent Acquisition, Total Rewards, People Analytics |
| Marketing | Chief Marketing Officer (L10) | | Brand & Communications, Growth Marketing |
| Legal & Compliance | General Counsel (L10) | | Legal, Compliance & Risk |

The CEO and the eight function heads sit in the Office of the CEO and are **executive officers**: counted in headcount, excluded from every pay figure. Department heads are sized to their department: VP (L9) for 1,000+ people, Senior Director (L8) for 300+, Director (L7) otherwise. Who leads which unit, and when, is recorded on the job history (`leads_org_unit_id`). The current chart with names and report counts: [org_chart.md](org_chart.md).

### Reporting rules

Every job record carries the worker's manager. The simulation keeps these rules true every day, and tests 24 to 27 check them at every month-end:

1. **Everyone reports to someone.** The CEO reports to the board; everyone else has a manager employed that day.
2. **Managers outrank their teams.** A people manager or director reports to someone at a higher level. An individual contributor reports to someone at the same level or higher (a Principal engineer can report to a Senior Manager).
3. **Teams stay inside their department.** Only org leaders report across units (a department head to their sub-function or function head).
4. **One leader per unit** at all times.

Not everyone is a people manager: about 12% of the company leads a team. Levels 1 to 4 are always individual contributors; levels 5 and 6 can be either (`Staff` / `Principal` or `Manager` / `Senior Manager`); level 7 and above always lead.

### How the org changes

| Event | What happens to the hierarchy |
|---|---|
| Hire | Placed under a manager in the department who can manage their level, preferring the closest level, a team under the cap and the same country |
| Manager leaves | 75% of the time the team is backfilled the next day: a senior team member steps up (L4s are promoted to L5), or an external manager is hired, and inherits the whole team. Otherwise the team is spread across other managers the next day |
| Department head leaves | Succession the next day: the most senior director steps up (promoted to the head's level if needed), or 35% of the time an external hire |
| Team grows past 9 | At month-end a senior team member becomes a manager and takes half the team; a director layer is added when a leader's team is mostly managers |
| Manager left with no team | Returns to individual-contributor work at month-end |
| Promotion past the manager's level | Moves to a manager who outranks them, the same day |
| Reorganization (Nov 2024) | Data & Analytics people in three engineering departments move into the new Data & AI Platform department under a new head; teams stay together where their manager moves too, and anyone left behind is reassigned the same day |

The result over four years: 25,014 → 30,024 people, 12–14% people managers, an average of 6.9 to 8.4 direct reports per manager, and eight layers from the CEO to the front line.

## Job levels and base salary

Each level has a base salary for a new hire in a US office at pay zone 1.00:

| Level | Name | Track | US base (USD) |
|---|---|---|---:|
| L1 | Associate | Individual contributor | 65,000 |
| L2 | Professional | Individual contributor | 82,000 |
| L3 | Senior | Individual contributor | 102,000 |
| L4 | Lead | Individual contributor | 125,000 |
| L5 | Staff / Manager | IC or people manager | 150,000 |
| L6 | Principal / Senior Manager | IC or people manager | 180,000 |
| L7 | Director | People leader | 220,000 |
| L8 | Senior Director | People leader | 265,000 |
| L9 | Vice President | People leader | 320,000 |
| L10 | Senior Vice President | Executive | 400,000 |
| L11 | Executive Vice President | Executive | 480,000 |
| L12 | Chief Executive Officer | Executive | 650,000 |

**Other countries** pay the US base × the country's pay index (Switzerland 1.12, Germany 0.86, United Kingdom 0.84, Spain 0.60, Poland 0.46, Brazil 0.36, India 0.27, Philippines 0.26 …), converted once at the ECB rates of 2022-06-30 and then **fixed in local currency** (`ref_job_level_base_salary`). An L4 in São Paulo is hired at BRL 234,900, in London at GBP 86,800, in Bengaluru at INR 2,668,100, whatever the exchange rate does later.

**Within a country**, offices carry a pay zone: San Francisco 1.15, New York 1.12, Seattle 1.10, Munich 1.05, Austin, Chicago and most offices 1.00, Vancouver 0.98, Hyderabad, Melbourne and Cape Town 0.97, Atlanta, Pune and Krakow 0.95, Guadalajara 0.92.

**A hire's salary** = level base × pay zone × an offer variation of up to ±10%. The range for every level runs from 85% to 135% of the base.

## How pay moves

| Change | Rule | Comp reason |
|---|---|---|
| **Tenure raise** | On every hire anniversary, by completed years of service: 1 year 5.0%, 2 years 6.0%, 3 years 5.0%, 4 years 4.5%, 5 years 4.0%, 6–10 years 3.0%, 11+ years 2.0% (`ref_tenure_increase`). Stops at the top of the range | Tenure Increase |
| **Promotion** | Exactly one level up, with an 8–12% raise (at least the new level's range minimum). Mainly on July 1 after the review; a few off-cycle | Promotion |
| **Demotion** | Exactly one level down, with a 3–8% cut; only after a Needs Improvement rating (8% of them) | Demotion |
| **Market adjustment** | 3–7%, off-cycle and rare (about 0.1% of people a month), capped at the range maximum | Market Adjustment |
| **Office move in the country** | Pay re-levelled by the pay-zone ratio | Relocation Adjustment |
| **Move to another country** | Pay converted to USD at that day's rate, re-levelled by the pay-index ratio, converted to the new currency | International Transfer |

Promotion and tenure raises are separate on purpose: base pay rises with tenure inside a level, and only a promotion changes the level. A new hire joins at the level base while a long-tenured colleague at the same level may be 20–30% above it, which is what makes "hires at lower pay replacing leavers at higher pay" a real driver in a compensation walk.

## Performance rating and bonus

Everyone employed on June 30 who joined by March 31 is rated for the fiscal year (`fact_performance_review`):

| Rating | Share of people | Bonus (% of base) | Effect on next year |
|---|---:|---:|---|
| Excellent | 20% | 25% | 22% chance of promotion; lower attrition |
| Good | 70% | 10% | 5.5% chance of promotion |
| Needs Improvement | 10% | 5% | No promotion; 8% chance of demotion; higher attrition |

Promotion to L6 is 40% less likely than to other levels. Ratings are sticky: an Excellent is more likely to be followed by another.

The bonus (`fact_bonus_payout`) is a one-time cash payment: base salary × FTE × bonus % × months worked in the fiscal year ÷ 12, in local currency, paid on August 31. People who leave before the payout date forfeit it. The FY2026 bonus is *Scheduled*: its payout date falls after the data window. Base salary and the tenure raise do not depend on the rating.

## Offices

35 offices in 22 countries, every region covered: North America 8, Latin America 3, Europe 12, Middle East & Africa 3, Asia Pacific 9. Six opened during the window: Manila (Oct 2022), Guadalajara (Mar 2023), Lisbon (Sep 2023), Seoul (Mar 2024), Pune (Jul 2024) and Vancouver (Jan 2025).

Street addresses are fictional. Postal codes are real codes for each business district, and coordinates are the [GeoNames](https://www.geonames.org/) centroid of that postal code (CC BY 4.0). Two exceptions, recorded in `geo_source`: GeoNames carries only city-level CEPs for Brazil, so São Paulo's point is the map location of CEP 04538-132 (Av. Brigadeiro Faria Lima, Itaim Bibi); and the UAE has no postal codes, so Dubai has none and its point is the Dubai International Financial Centre.

## Currency

All FX rates are the **European Central Bank's euro foreign exchange reference rates**, published every TARGET business day ([`reference/`](../../reference/README.md)). Arcadia reports in USD, so each rate is crossed through the euro: `USD per local = (USD per EUR) ÷ (local per EUR)`. The UAE dirham is not in the ECB basket and uses its USD peg (AED 3.6725 since 1997). On days with no ECB rate, the latest rate on or before the date applies.

Pay is held in local currency and stated in USD three ways:

| Basis | Rate used | Where | Moves when |
|---|---|---|---|
| **Nominal (month-end)** | The rate on each month-end | Snapshot, cost bridge, cost snapshot | Pay changes, or the currency moves |
| **Posting (booked)** | The rate on the day the pay record took effect | `int_compensation_history_usd`, snapshot | Only when a new pay record is posted |
| **Constant** | One rate set for all periods: the latest month-end in the data, 2026-06-30 | Snapshot, cost bridge, cost snapshot | Only when pay changes |

Nominal answers "what does the payroll cost in dollars today", posting answers "what did we commit to in dollars when we set the pay", and constant answers "how much did pay itself change". At the 2026-06-30 month-end, nominal and constant agree by construction (test 11).

## Fringe rates

Fringe is what the employer pays on top of base salary, as a share of base salary. It varies by country and changes with the law, so it is researched by country and **calendar year** (rates change on January 1) for 2022–2026, in four components (`ref_fringe_rate`):

| Component | What it covers | Examples |
|---|---|---|
| Social contributions | Statutory employer social security and payroll taxes | US FICA and unemployment taxes, German pension/health/unemployment/care insurance, UK employer NIC and Apprenticeship Levy |
| Retirement and severance | Mandatory pension, provident, severance or gratuity funding outside social security | Brazil FGTS, Australia superannuation guarantee, Swiss BVG, Korea severance, India PF and gratuity, Singapore CPF, UK and Irish auto-enrolment, UAE end-of-service gratuity |
| Statutory pay | Pay the law adds beyond 12 monthly salaries | Brazil 13th salary and one-third vacation bonus, Mexico aguinaldo and vacation premium, Philippines 13th month |
| Employer benefits | Employer health and retirement benefits | **US only**, where they take the place of public systems |

Voluntary benefits outside the US (private medical, top-up pensions, meal vouchers) are a company's choice, not a country cost, and are left out.

### Method

- **OECD members other than the US** (15 of the 22 countries): employer social security contributions, including payroll taxes, for a single worker at 100% of the average wage, from OECD *Taxing Wages* Table 1.2. The OECD states them as a share of labour costs; they are converted to a share of gross wages as `L ÷ (100 − L)`. Each year comes from the edition that first reported it (2023 edition for 2022 … 2026 edition for 2025).
- **2026 for OECD members:** the 2027 edition is not out yet, so 2025 is carried forward and flagged `is_estimate`, except where a 2026 statutory change was confirmed and added: Germany (average additional health contribution 2.5% → 2.9%), Spain (intergenerational equity mechanism 0.67% → 0.75% for employers), Ireland (PRSI 11.25% from October 2025 and 11.40% from October 2026) and Korea (national pension 9% → 9.5%, health insurance 7.09% → 7.19%).
- **United States:** BLS *Employer Costs for Employee Compensation*, private industry, management, professional and related occupations, March of each year. Base salary pays for time worked and paid leave, so each component is divided by wages and salaries plus paid leave: legally required benefits are the social contributions; insurance plus retirement and savings are the employer benefits.
- **Contribution ceilings** (UK pension band, Swiss BVG, Singapore CPF, Philippines SSS/PhilHealth/Pag-IBIG, South Africa UIF, India EDLI) are evaluated at a reference salary: Arcadia's L4 base in that country.
- **Arcadia pay policy where the law sets charges on "basic" pay:** India's basic is 50% of base salary (which also meets the 50% wage rule of the labour codes in force since 21 November 2025); the UAE's basic is 60%.
- **Brazil** uses the standard payroll regime (not Simples Nacional or the sector payroll-tax relief), with RAT at 2% and the FAP factor at 1.0. Its charges are also due on the 13th salary and vacation bonus, which is why the total reaches 50.9%.

### Results

| Country | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|
| **Asia Pacific** | | | | | |
| Australia | 15.6% | 16.8% | 17.3% | 17.8% | 18.0%* |
| India | 8.5% | 8.5% | 8.5% | 8.5% | 8.5% |
| Japan | 15.3% | 15.6% | 15.7% | 15.6% | 15.6%* |
| Philippines | 10.9% | 11.4% | 12.1% | 12.5% | 12.5% |
| Singapore | 8.3% | 8.4% | 9.3% | 10.2% | 11.0% |
| South Korea | 19.3% | 19.4% | 19.4% | 19.4% | 19.8% |
| **Europe** | | | | | |
| France | 36.4% | 36.2% | 36.4% | 36.4% | 36.4%* |
| Germany | 19.9% | 20.1% | 20.2% | 20.9% | 21.1% |
| Ireland | 11.1% | 11.1% | 11.1% | 11.2% | 12.8% |
| Netherlands | 12.0% | 12.0% | 12.1% | 12.6% | 12.6%* |
| Poland | 16.4% | 16.4% | 16.4% | 16.3% | 16.3%* |
| Portugal | 23.8% | 23.8% | 23.8% | 23.8% | 23.8%* |
| Spain | 29.9% | 30.4% | 30.6% | 30.6% | 30.6% |
| Sweden | 31.4% | 31.4% | 31.4% | 31.4% | 31.4%* |
| Switzerland | 8.6% | 8.7% | 8.7% | 8.8% | 8.8%* |
| United Kingdom | 13.6% | 13.2% | 13.4% | 15.7% | 15.7%* |
| **Latin America** | | | | | |
| Brazil | 50.9% | 50.9% | 50.9% | 50.9% | 50.9% |
| Mexico | 16.0% | 16.2% | 15.9% | 15.8% | 15.8%* |
| **Middle East & Africa** | | | | | |
| South Africa | 1.3% | 1.3% | 1.3% | 1.3% | 1.3% |
| United Arab Emirates | 3.5% | 3.5% | 3.5% | 3.5% | 3.5% |
| **North America** | | | | | |
| Canada | 9.2% | 9.2% | 9.5% | 9.7% | 9.7%* |
| United States | 22.1% | 21.9% | 21.9% | 21.9% | 22.4% |

\* 2025 rate carried forward; the OECD has not published 2026 yet.

How the 2026 totals break down (% of base salary):

| Country | Social contributions | Retirement & severance | Statutory pay | Employer benefits | Total |
|---|---:|---:|---:|---:|---:|
| Brazil | 30.9 | 8.9 | 11.1 | | **50.9** |
| France | 36.4 | | | | **36.4** |
| Sweden | 31.4 | | | | **31.4** |
| Spain | 30.6 | | | | **30.6** |
| Portugal | 23.8 | | | | **23.8** |
| United States | 8.3 | | | 14.2 | **22.4** |
| Germany | 21.1 | | | | **21.1** |
| South Korea | 11.4 | 8.3 | | | **19.8** |
| Australia | 6.0 | 12.0 | | | **18.0** |
| Poland | 16.3 | | | | **16.3** |
| Mexico | 10.9 | | 4.9 | | **15.8** |
| United Kingdom | 14.1 | 1.5 | | | **15.7** |
| Japan | 15.6 | | | | **15.6** |
| Ireland | 11.3 | 1.5 | | | **12.8** |
| Netherlands | 12.6 | | | | **12.6** |
| Philippines | 4.2 | | 8.3 | | **12.5** |
| Singapore | 0.1 | 10.9 | | | **11.0** |
| Canada | 9.7 | | | | **9.7** |
| Switzerland | 6.4 | 2.4 | | | **8.8** |
| India | | 8.5 | | | **8.5** |
| United Arab Emirates | | 3.5 | | | **3.5** |
| South Africa | 1.3 | | | | **1.3** |

What the research shows, and what it changes in the data:

- **The law moves fringe more than policy does.** The UK's April 2025 employer NIC increase (13.8% to 15% above a lower threshold) lifts UK fringe from 13.4% to 15.7%; Australia's superannuation guarantee steps from 10% to 12% between 2022 and 2025; Singapore's CPF salary ceiling rises every year to 2026; Ireland adds pension auto-enrolment in 2026.
- **Low statutory charges are real.** South Africa (UIF capped at ZAR 177 a month plus a 1% skills levy) and the UAE (no social security for expatriates, only the end-of-service gratuity) cost little on top of salary. Companies there usually add private medical and retirement plans, which this model leaves out by design.
- **The US is mostly benefits.** Legally required charges are about 8% of pay; employer health insurance and retirement plans add another 14%.

### Sources

Every component cites at least one source in `ref_fringe_source`; test 28 fails the build if one is missing.

| ID | Source |
|---|---|
| `OECD-TW23` | [OECD, Taxing Wages 2023, Table 1.2 (2022 data)](https://www.oecd.org/en/publications/taxing-wages-2023_8c99fa4d-en/full-report/component-4.html) |
| `OECD-TW24` | [OECD, Taxing Wages 2024, Table 1.2 (2023 data)](https://www.oecd.org/en/publications/taxing-wages-2024_dbcbac85-en/full-report/component-4.html) |
| `OECD-TW25` | [OECD, Taxing Wages 2025, Table 1.2 (2024 data)](https://www.oecd.org/en/publications/taxing-wages-2025_b3a95829-en/full-report/overview_715add19.html) |
| `OECD-TW26` | [OECD, Taxing Wages 2026, Table 1.2 (2025 data)](https://www.oecd.org/en/publications/taxing-wages-2026_3a5169ef-en/full-report/overview_d93131c3.html) |
| `BLS-2022` … `BLS-2026` | BLS, Employer Costs for Employee Compensation, March [2022](https://www.bls.gov/news.release/archives/ecec_06162022.pdf), [2023](https://www.bls.gov/news.release/archives/ecec_06162023.htm), [2024](https://www.bls.gov/news.release/archives/ecec_06182024.pdf), [2025](https://www.bls.gov/news.release/archives/ecec_06132025.htm), [2026](https://www.bls.gov/news.release/archives/ecec_06122026.htm), Table 4 |
| `DE-2026` | [German social insurance rates 2026](https://lohn-info.de/sozialversicherungsbeitraege2026.html) |
| `ES-MEI` | [Spain intergenerational equity mechanism (MEI) schedule 2023–2029](https://institutosantalucia.es/actualidad/seguridad-social/mei-que-es-y-como-afecta-a-tu-nomina/) |
| `IE-PRSI` | [Ireland employer PRSI 11.25% from October 2025](https://payroll.org/news-resources/news/news-detail/2026/01/05/ireland-s-budget-2026-brings-significant-changes-for-payroll) |
| `IE-2026` | [Ireland My Future Fund auto-enrolment from 1 January 2026](https://brightsg.com/blog/my-future-fund-prsi-budget-2026/) |
| `KR-2026` | [Korea 2026 national pension and health insurance rates](https://www.crowe.com/kr/en-us/news/news20260101_en) |
| `KR-SEV` | [Korea statutory severance: 30 days' average wage per year of service](https://www.atlashxm.com/resources/employee-benefits-in-south-korea) |
| `UK-AE` | [UK workplace pension: employer minimum 3% of qualifying earnings](https://www.gov.uk/workplace-pensions/what-you-your-employer-and-the-government-pay) |
| `UK-LEVY` | [UK Apprenticeship Levy: 0.5% of pay bill](https://www.gov.uk/guidance/pay-apprenticeship-levy) |
| `CH-BVG-22`, `CH-BVG-25` | Swiss BVG key figures [2022–2023](https://finpension.ch/?p=8671) and [2025–2026](https://www.allianz.ch/content/dam/onemarketing/azch/common/allianz/en/bvg/allianz-api-key-opi-figures-interest-conversion-rates.pdf) |
| `AU-SG` | [Australia superannuation guarantee schedule](https://australiansuper.com/superannuation/superannuation-articles/2024/07/understanding-the-superannuation-guarantee) |
| `MX-LFT` | [Mexico Federal Labor Law, art. 87: aguinaldo of at least 15 days' pay](https://www.diputados.gob.mx/LeyesBiblio/pdf/LFT.pdf) |
| `MX-VAC` | [Mexico vacation reform: 12 days from 1 January 2023, 25% vacation premium](https://global.lockton.com/us/en/news-insights/mexico-to-increase-paid-vacation-days-for-all-employees) |
| `BR-STAT` | [Brazil employer payroll charges](https://www.globalexpansion.com/countrypedia/Brazil) |
| `AE-EOSG` | [UAE Decree-Law 33/2021: end-of-service gratuity](https://www.morganlewis.com/pubs/2021/12/united-arab-emirates-updates-federal-labour-law) |
| `ZA-PWC` | [PwC Worldwide Tax Summaries, South Africa: other taxes](https://taxsummaries.pwc.com/south-africa/corporate/other-taxes) |
| `IN-EPF` | [Employees' Provident Funds Act 1952 and Payment of Gratuity Act 1972](https://www.epfindia.gov.in/) |
| `IN-CODES` | [India labour codes in force from 21 November 2025](https://www.littler.com/news-analysis/asap/indias-labor-law-overhaul-snapshot-key-changes) |
| `SG-CPF` | [CPF Board: monthly salary ceiling 2023–2026](https://cpf.gov.sg/member/infohub/news/media-news/budget-2023-cpf-monthly-salary-ceiling-to-be-raised-to-8000-by-2026) |
| `SG-SDL` | [Skills Development Levy](https://gobusiness.gov.sg/about-skills-development-levy) |
| `PH-SSS23` | [Philippines SSS contribution schedule 2023 vs 2021–2022](https://forvismazars.com/ph/en/insights/hr-payroll-alerts/new-sss-contribution-rates-for-2023) |
| `PH-PWC` | [PwC Worldwide Tax Summaries, Philippines: SSS, PhilHealth, Pag-IBIG](https://taxsummaries.pwc.com/philippines/individual) |
| `PH-13M` | [Philippines Presidential Decree 851: 13th month pay](https://www.dole.gov.ph/) |

The research is code, not a spreadsheet: [`generator/fringe_research.py`](../../generator/fringe_research.py) holds every input with its source and builds both tables; `python generator/fringe_research.py` prints the result.
