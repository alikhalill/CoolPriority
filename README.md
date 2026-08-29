Markdown
# 🌡️ CoolPriority

> **Turning hyperlocal heat intelligence into actionable cooling-resource decisions.**

CoolPriority is an AI-powered heat decision-support system built for the **FortyGuard Hackathon'26**.
It combines **FortyGuard hyperlocal temperature intelligence**, **CDC/ATSDR Social Vulnerability Index (SVI) 2022**, **population context**, **transit locations**, and **scenario-based resource planning** to help decision-makers determine:

**WHERE should we act? WHO needs attention? WHEN is heat most intense? WHAT intervention could be considered? HOW MUCH can we achieve with a limited budget?**

---

## 🏆 Hackathon Track

CoolPriority is primarily aligned with:
**Government & Environment — interactive heat maps for planning and safety**

It also has strong relevance to:
**Industrial & Enterprise — dashboards turning heat data into decisions**

The project uses the **FortyGuard Temperature API** as a core environmental data source.

---

## 🚨 Problem

Extreme heat is not experienced equally across an urban area.
A heat map can identify hot locations, but a city still needs to answer a harder operational question:

> **Where should limited cooling resources be deployed first?**

Temperature alone is not enough. A practical planning system should consider:
- Heat intensity
- Heat exposure
- Social vulnerability
- Population reach
- Timing of peak heat
- Accessibility / transit context
- Available intervention budget
- Alternative policy objectives

CoolPriority transforms these signals into an interpretable decision workflow.

---

## 💡 Solution

CoolPriority turns raw temperature intelligence into a resource-allocation recommendation.

```text
FortyGuard Hyperlocal Heat
            ↓
       Heat Exposure
            ↓
   Census Tract Spatial Join
            ↓
        SVI 2022
            ↓
   Social Vulnerability
            ↓
     Cooling Priority
            ↓
        Population
            ↓
     Policy Selection
            ↓
      Budget What-If
            ↓
     Marginal Benefit
            ↓
   Recommended Allocation
🧠 Core Decision Engine
CoolPriority does not treat heat as a single-variable problem.
The system combines multiple dimensions into a normalized Cooling Priority Score.

Conceptually:

Plaintext
Cooling Priority
        =
Heat Exposure
        +
Social Vulnerability
        +
Population Context
        ↓
Cooling Priority Score
        ↓
Population Reach
        ↓
Impact Score
        ↓
Policy & Budget Optimization
The system keeps the individual indicators visible so that each recommendation can be interpreted and explained.

📊 Main Outputs
For every analyzed Census Tract, CoolPriority can provide:

Heat Exposure Score

Social Vulnerability Score

Cooling Priority Score

Population

Population Percentile

Priority Label

Impact Score

Geographic location

Recommended policy allocation

These outputs are used by the application to move from environmental data to actionable planning.

🔄 End-to-End Workflow
Plaintext
1. FortyGuard Heatmap
          ↓
2. Hyperlocal Temperature Data
          ↓
3. Census Tract Spatial Analysis
          ↓
4. SVI 2022 Integration
          ↓
5. Heat + Vulnerability Analysis
          ↓
6. Cooling Priority Calculation
          ↓
7. Population Integration
          ↓
8. Transit Heat Overlay
          ↓
9. Peak Heat Timing
          ↓
10. Intervention Simulation
          ↓
11. Policy Comparison
          ↓
12. Budget What-If Analysis
          ↓
13. Marginal Benefit
          ↓
14. Recommended Allocation
          ↓
15. Interactive Streamlit Dashboard
🗺️ Spatial Analysis
CoolPriority works at the Census Tract level.
The workflow spatially connects environmental, demographic, and geographic information.
Main geographic inputs include:

New York Census Tract boundaries

FortyGuard heatmap cells

CDC/ATSDR SVI 2022

Population data

MTA station locations

This allows the system to transform raw spatial information into tract-level decision indicators.

🌡️ FortyGuard Heat Intelligence
FortyGuard is the environmental intelligence layer of CoolPriority.
The project retrieves hyperlocal temperature information and uses it for spatial and temporal analysis.

The analyzed heatmap contains:

150 FortyGuard heatmap features

Example modeled temperature statistics:

Minimum: approximately 29.74°C

Maximum: approximately 30.67°C

Mean: approximately 30.01°C

The system also validates the structure of FortyGuard responses before processing them.
The API response is handled through:

Plaintext
map_data
    └── features
This validation helped make the live-analysis component more robust when the API returned an empty or differently structured response.

🧑‍🤝‍🧑 Social Vulnerability
Temperature alone does not describe the full impact of extreme heat.
CoolPriority integrates CDC/ATSDR SVI 2022 to provide social vulnerability context.
The SVI information is spatially matched with Census Tracts and incorporated into the prioritization workflow.
This helps identify locations where heat exposure overlaps with higher vulnerability.

👥 Population Reach
Population provides another important planning dimension.
The system calculates how many people could potentially be reached by different resource-allocation strategies.
This allows decision-makers to compare:

Higher Priority Concentration vs. Larger Population Reach

rather than optimizing for only one objective.

🚇 Transit Heat Overlay
CoolPriority integrates MTA station locations to add an accessibility and mobility layer.
The tested MTA dataset contained:

496 records before deduplication

493 unique physical stations

3 duplicate records removed

21 stations matched with priority areas

Example high-priority transit location:

Chambers St

Tract: 29.01

Cooling Priority: 95.24

Heat Exposure: 96.31

Social Vulnerability: 92.77

This layer can help identify transit locations that overlap with high-priority heat areas.

⏰ Peak Heat Timing
CoolPriority also analyzes when modeled heat reaches its peak.
Using FortyGuard time-of-measure data:

Total tiles: 150

Most common peak hour: 16:00 UTC

Tiles at peak hour: 147 / 150

Peak-hour share: 98%

Peak range: 15:00–16:00 UTC

This provides temporal context for operational planning. For example, decision-makers can consider when resources, alerts, or cooling services should be most active.

🏗️ Intervention Simulator
The intervention simulator evaluates potential intervention scenarios.
Current modeled scenarios include:

Intervention	Modeled Priority Reduction
No Intervention	0%
Urban Trees / Shade	8%
Cool Roofs	6%
Cooling Center	12%
These values are scenario assumptions used for comparative decision support. They are not guarantees of actual physical temperature reduction.

The simulator follows:

Plaintext
Baseline Priority
        ↓
Intervention Scenario
        ↓
Simulated Priority
        ↓
Priority Reduction
💰 Resource Allocation
CoolPriority supports resource allocation under a limited intervention budget.
Three policy strategies are currently implemented:

Need-First: Prioritizes the areas with the highest cooling need.

Balanced: Balances cooling need with population reach.

Reach-First: Prioritizes larger population reach while retaining a meaningful heat/vulnerability signal.

For example, with a budget of 3:

Policy	Population Coverage	Priority Coverage	Impact
Need-First	16.28%	44.98%	225.83
Balanced	24.71%	41.91%	209.09
Reach-First	35.41%	32.03%	215.65
This demonstrates the trade-off between maximizing priority coverage and maximizing population reach.

💵 Budget What-If Analysis
The system can simulate different intervention budgets.
Tested budgets include: 1 → 2 → 3 → 4 → 5 → 6 → 7

For each budget and policy, CoolPriority calculates:

Population Coverage

Priority Coverage

Impact Score

Selected Areas

Coverage gains

This allows decision-makers to ask: What can we achieve if the available budget changes?

📈 Marginal Benefit
The system also measures the value of one additional intervention.
For example, when increasing the budget from 3 to 4:

Policy	Population Gain	Priority Gain	Impact Gain
Need-First	+12.21%	+10.73%	+63.00
Balanced	+3.78%	+13.80%	+57.00
Reach-First	+14.92%	+3.34%	+67.48
This creates a Value of One More Intervention view.

🧭 Explainable Policy Recommendations
CoolPriority does not simply output a location. It explains why an area or policy was selected.
The recommendation can be based on the decision-maker's objective:

Objective: Priority → Need-First

Objective: Population → Reach-First

Objective: Balanced → Best-performing policy according to the tested metrics

This makes the system more transparent and easier to use for planning.

🖥️ Interactive Streamlit Application
The Streamlit application brings the main components together into an interactive interface.
The intended decision workflow is:

Plaintext
Select / Explore Area
        ↓
View Heat Conditions
        ↓
View Vulnerability
        ↓
View Population
        ↓
View Cooling Priority
        ↓
Explore Transit Context
        ↓
Choose Budget
        ↓
Compare Policies
        ↓
Explore Interventions
        ↓
Review Recommendation
The goal is to provide a decision-support experience rather than simply displaying a static heat map.

🔐 Security
API credentials are stored through environment variables.
The real .env file is excluded using .gitignore.
The repository contains an .env.example, but the actual API key should never be committed to GitHub.

🧪 Validation & Testing
The project contains dedicated testing scripts for the main analytical components. Validated components include:

FortyGuard heatmap retrieval

Heatmap response validation

Heat burden analysis

SVI integration

Census tract spatial matching

Cooling priority calculation

Resource allocation

Policy comparison

Budget scenarios

Marginal benefit

Intervention simulation

Transit heat overlay

Time-of-measure analysis

Peak heat timing

Live analysis

Where possible, saved FortyGuard responses are reused for analysis and testing to avoid unnecessary API calls and preserve available hackathon credits.

📂 Project Structure
Plaintext
CoolPriority/
│
├── app.py
│
├── src/
│   ├── fortyguard.py
│   ├── cooling_priority.py
│   └── live_analysis.py
│
├── data/
│   ├── SVI_2022_US.csv
│   └── ny_tracts/
│
├── aggregate_tract_priority.py
├── census_population.py
├── spatial_join_svi.py
├── prepare_map_data.py
│
├── analyze_heat_burden_distribution.py
├── compare_heat_analytics.py
├── priority_explanation.py
│
├── resource_allocation.py
├── resource_allocation_v2.py
├── resource_allocation_v3.py
├── policy_comparison.py
├── budget_scenario.py
├── budget_scenario_v2.py
│
├── intervention_simulator.py
├── heat_trajectory.py
├── transit_heat_overlay.py
├── time_of_measure.py
├── peak_heat_timing.py
│
└── test_*.py
⚠️ Modeling Disclaimer
CoolPriority is a hackathon decision-support prototype. The intervention simulator uses modeled assumptions and should not be interpreted as a guaranteed prediction of real-world intervention outcomes. The Cooling Priority Score is also a model-generated prioritization signal rather than a direct measurement of health risk. The purpose of the system is to provide a transparent framework for comparing locations, policies, budgets, and potential interventions.

🚀 Future Improvements
Potential future improvements include:

More detailed intervention cost models

Real cooling-center locations

Additional transportation layers

Real-time weather integration

Historical heat comparisons

Improved temporal forecasting

Multi-objective optimization

More detailed demographic modeling

Intervention effectiveness calibration

Automated scenario recommendations

Production deployment

🏆 Why CoolPriority?
Traditional heat maps answer: Where is it hot?
CoolPriority asks a more actionable question: Where is heat most urgent, who is affected, when is heat highest, where can resources reach the most people, and what can we achieve with a limited budget?

The system connects environmental intelligence with vulnerability, population, policy, budget, and intervention planning.

Plaintext
Heat Intelligence
        ↓
  Vulnerability
        ↓
    Population
        ↓
     Priority
        ↓
      Policy
        ↓
      Budget
        ↓
   Intervention
        ↓
      Action
👥 Team
CoolPriority — FortyGuard Hackathon'26
A collaborative decision-support prototype focused on heat resilience, environmental intelligence, and resource planning.

📌 Disclaimer
CoolPriority is a hackathon prototype intended for research, demonstration, and decision-support purposes. It should not replace official emergency-management guidance, public-health recommendations, engineering analysis, or professional policy decisions.

Final Concept: CoolPriority transforms hyperlocal heat intelligence into explainable, population-aware, budget-constrained cooling-resource decisions.