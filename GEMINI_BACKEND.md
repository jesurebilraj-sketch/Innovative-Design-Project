# SkyOps Backend — Gemini CLI Project Context

## 0. Purpose of this file

This file is the persistent instruction/context for Gemini CLI when working on the **SkyOps AI-Powered Aviation Operations Platform backend**.

Treat this document as the backend source of truth together with the code already present in the repository.

The backend must be implemented as a **correct, deterministic, testable decision-support system** that exposes aviation data, consumes weather data, consumes ML predictions, calculates delay propagation, and recommends/reassigns gates without violating operational constraints.

Do not redesign the whole project unless explicitly asked.

---

# 1. Backend-only scope

This repository/workstream is the backend.

Primary responsibilities:

- FastAPI application
- REST API routing
- Supabase/PostgreSQL persistence
- SQL/repositories
- ORM/database models
- Pydantic schemas
- Authentication/authorization integration
- Weather API integration
- Flight data handling
- Prediction-service integration
- Gate availability/presence calculations
- Gate assignment/recommendation
- Gate reassignment after disruptions
- Aircraft turnaround pairing
- Delay propagation across rotations
- Analytics aggregation APIs
- Validation and error handling
- Tests
- Docker/local deployment configuration
- API and architecture documentation

Out of scope for backend implementation:

- ML model training
- Dataset experimentation notebooks
- CatBoost hyperparameter tuning
- Feature-selection experiments performed for model training
- ANN/LSTM/XGBoost training
- Frontend implementation

The backend may contain the **predictor interface/adapter and inference integration**, but it must not silently become the ML training project.

Do not modify unrelated ML-training or frontend files unless explicitly requested.

---

# 2. Current project idea

SkyOps is intended to move from:

    Flight data + weather data
            -> prediction
            -> operational analysis
            -> gate recommendation

The practical backend flow is:

    Flight/event data
          |
          v
    PostgreSQL / Supabase
          |
          +---- Weather adapter (Open-Meteo)
          |
          +---- Prediction adapter
          |
          v
    Backend services
          |
          +---- delay interpretation
          +---- delay propagation
          +---- turnaround mapping
          +---- gate presence/availability
          +---- gate recommendation/reassignment
          +---- analytics
          |
          v
    REST responses

The backend is the central application layer. Prediction is an input to operational logic, not a replacement for it.

---

# 3. Required architecture

Use a layered structure:

    API endpoint
        -> Pydantic schema / validation
        -> Service / use case
        -> Repository / domain / integration
        -> Database or external provider

Endpoints should be thin.
Business rules belong in services/domain modules.
SQL belongs in repositories.
External APIs belong in integrations/adapters.
Pure algorithms should not import FastAPI, SQLAlchemy, or Supabase-specific code.

Recommended project structure:

```text
skyops-backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── health.py
│   │           ├── airports.py
│   │           ├── flights.py
│   │           ├── predictions.py
│   │           ├── gates.py
│   │           ├── weather.py
│   │           └── analytics.py
│   │
│   ├── schemas/
│   ├── services/
│   │   ├── prediction.py
│   │   ├── gate_recommendation.py
│   │   ├── weather.py
│   │   └── analytics.py
│   │
│   ├── domain/
│   │   ├── ports.py
│   │   ├── presence.py
│   │   ├── gate_assignment.py
│   │   ├── propagation.py
│   │   └── turnarounds.py
│   │
│   ├── repositories/
│   ├── db/
│   ├── integrations/
│   │   ├── weather.py
│   │   └── predictor.py
│   └── core/
│       ├── settings.py
│       ├── logging.py
│       └── exceptions.py
│
├── alembic/
├── scripts/
│   └── seed_db.py
├── tests/
├── docs/
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── .env.example
├── pyproject.toml
└── README.md
```

Do not create duplicate layers just because another pattern is fashionable.
Inspect existing code first.

---

# 4. Research basis that the backend must understand

The following seven research papers were used as the basis of the SkyOps research direction. The backend must understand their operational ideas so that implementation does not contradict the research.

Important: these papers are research foundations. **Do not blindly copy a research paper's full optimization/training implementation into the application.** The SkyOps backend is intended to be a practical, lightweight decision-support system.

---

# 5. Paper 1 — Sternberg et al. — A Review on Flight Delay Prediction (2017)

Authors in the original preprint:
Alice Sternberg, Jorge Soares, Diego Carvalho, Eduardo Ogasawara.

The paper is a literature review rather than one single predictive model. It organizes the flight-delay prediction problem by problem type, scope, data, and computational method.

## 5.1 Definition of delay

A basic definition is the difference between scheduled and actual departure/arrival time:

    delay = actual_time - scheduled_time

For example:

    scheduled arrival = 14:00
    actual arrival    = 14:25
    arrival delay     = 25 minutes

Be careful about negative values. A flight arriving before its scheduled time has a negative deviation, which is not automatically the same as "on time" in every operational convention. Preserve the raw deviation and apply any project-specific classification rule separately.

## 5.2 Three major problem categories

The review distinguishes:

1. Root/new delay — predicting when/where delay will occur and its causes.
2. Delay propagation — an existing delay affecting subsequent flights/resources.
3. Cancellation — conditions leading to cancellation and the associated decision process.

SkyOps mainly combines root-delay prediction with delay propagation and operational gate decisions.

## 5.3 Data taxonomy important to backend design

The paper groups useful information into major dimensions:

- Spatial: origin, destination, airport, city, region.
- Temporal: season, month, day of week, time of day.
- Weather: visibility, ceiling, surface weather, en-route weather.
- Planning: airline schedules, airport schedules, flight plans.
- Features: airline status, aircraft model/size, occupancy, airport infrastructure, frequency.
- State: prior delay levels and current operational conditions.
- Operations: airport/airspace capacity and demand.

This taxonomy is directly useful when designing database entities and API payloads.

## 5.4 Data-management concepts

The review identifies data cleaning, feature selection, transformation, normalization/discretization, clustering, ETL, and data integration as recurring tasks.

Backend implication:

- store normalized timestamps;
- maintain airport identifiers consistently;
- store raw operational data where useful;
- never mix local timezone timestamps without an explicit timezone;
- retain enough historical data to reproduce a prediction request;
- distinguish raw observations from derived metrics.

## 5.5 Practical lesson for SkyOps

The review does **not** provide a single formula or model to implement. Its main backend lesson is architectural: aviation prediction depends on multiple dimensions and multiple data sources. Therefore the backend must be able to combine flight, weather, temporal, spatial, state, and infrastructure data.

Source:
https://arxiv.org/abs/1703.06118

---

# 6. Paper 2 — Huo et al. — The Prediction of Flight Delay: Big Data-Driven Machine Learning Approach (2020)

Data/context:
- Hong Kong International Airport.
- 2018 airline data.
- 29,352 flight records were split into 80/20 training/test data.
- 161 airports appear in the dataset.
- Diverted flights were removed.
- Scheduled and actual departure/arrival times, delay/cancellation information, travel time, distance, origin, destination, and airline information were considered.

The study compared several classifiers including Random Forest, Logistic Regression, K-nearest Neighbors, Decision Tree, and Naive Bayes.

## 6.1 Feature categories used

Core examples:

- month;
- day of week;
- departure time;
- arrival time;
- origin airport;
- destination airport;
- distance;
- carrier.

Additional attributes explored included:

- average taxi time;
- airline group;
- block time;
- distance;
- aircraft group size.

The study reported that adding these features changed model performance, with distance and block time providing substantial signal in its experiments.

## 6.2 Random Forest feature importance formula used in the paper

The paper gives a feature-importance calculation based on node split quantities. Its notation is approximately:

    f_i = (sum of split-related node quantities for feature i)
          / (sum over all nodes of the corresponding quantities)

The forest-level importance is then averaged over trees:

    RF_f_i = (sum of normalized feature importance for feature i over all trees) / T

where T is the number of trees.

Backend implication:
Do not calculate or store feature importance during every API request. Feature importance is a model-analysis concern. The backend may expose a precomputed model explanation if the ML component supplies it.

## 6.3 Logistic regression formula

The paper presents the logistic function:

    sigma(t) = 1 / (1 + exp(-t))

with:

    t = beta_0 + beta_1*x

and therefore:

    p(x) = 1 / (1 + exp(-(beta_0 + beta_1*x)))

Interpretation:
The output is a probability in [0, 1] for a binary event such as delayed/on-time.

This is background theory only. Do not implement Logistic Regression in the backend unless explicitly requested.

## 6.4 KNN distance

The paper lists distance forms including:

Euclidean:

    d(x,y) = sqrt(sum_i (x_i - y_i)^2)

Manhattan:

    d(x,y) = sum_i |x_i - y_i|

General Minkowski:

    d(x,y) = (sum_i |x_i - y_i|^q)^(1/q)

Again, these explain the research foundation; they are not backend gate-distance formulas.

## 6.5 Decision-tree regression/classification concept

The paper expresses a tree output conceptually as an expectation over the leaf reached by x:

    f(x) = E[y | x]

with leaf/path conditions determining the relevant terminal value.

## 6.6 Backend lesson

The key lesson is that flight delay prediction requires useful operational attributes, not merely a flight number. The API/database model should preserve the fields needed to reconstruct a prediction context: time, route, airline, aircraft, distance, prior delay/state, and weather when available.

Source:
https://ira.lib.polyu.edu.hk/handle/10397/89846

---

# 7. Paper 3 — Zhang et al. — Spatio-Temporal Data Mining for Aviation Delay Prediction (2021)

Authors:
Kai Zhang, Yushan Jiang, Dahai Liu, Houbing Song.

Core idea:
Aviation delay is not purely a static/tabular problem. It has spatial and temporal dependencies. The paper uses a stacked LSTM model with ADS-B trajectory data and weather/airspace/ATC information.

## 7.1 Problem formulation

A sequence of observations is treated as:

    X_F^A = {x_t}_{t=1}^N

where x_t is an M-dimensional feature vector.

The sequence is mapped to a future target:

    f(X_F^A) -> Y_F^A

The paper uses a future prediction horizon tau. In its experiment, tau is set to 60 minutes.

## 7.2 LSTM equations

Forget gate:

    f_t = sigma(W_f [h_(t-1), x_t] + b_f)

Input gate:

    i_t = sigma(W_i [h_(t-1), x_t] + b_i)

Candidate cell state:

    C~_t = tanh(W_C [h_(t-1), x_t] + b_C)

Cell-state update:

    C_t = f_t * C_(t-1) + i_t * C~_t

Output gate:

    o_t = sigma(W_o [h_(t-1), x_t] + b_o)

Hidden state:

    h_t = o_t * tanh(C_t)

where sigma is the sigmoid function and * is element-wise multiplication.

Backend meaning:
The backend must be able to store/serve time-ordered observations if a future temporal model needs them. The backend does not train the LSTM.

## 7.3 Data sources used

The paper integrates:

- flight data;
- ADS-B trajectory data;
- ATC/ARTCC data;
- weather data.

Trajectory fields include longitude, latitude, altitude, speed, track angle, aircraft identification/model information.

## 7.4 Feature engineering concepts

The study removes variables with more than 80% missing values and checks pairwise Pearson correlation, removing redundant variables beyond an 80% correlation threshold.

Ground congestion is represented by counting arrivals/departures in 10-minute bins.

Airspace congestion is represented by counting aircraft in relevant geographic/altitude sectors.

High-cardinality categorical variables use frequency encoding; low-cardinality variables use one-hot encoding.

## 7.5 Haversine distance

For geographic distance between two latitude/longitude points, the paper uses the great-circle Haversine formula:

    d = 2r * asin( sqrt( sin^2(Delta_phi/2)
                         + cos(phi_1) cos(phi_2) sin^2(Delta_psi/2) ) )

where:

    Delta_phi = phi_2 - phi_1
    Delta_psi = psi_2 - psi_1
    r = Earth radius

Backend use:
This is useful for airport/gate/flight geographic calculations where coordinates are available. Always use radians in trigonometric functions.

## 7.6 Backend lesson

Do not reduce the data model to a single delay column. Preserve event time, geography, airport, route, weather, prior operational state, and aircraft identity where available.

For an API, all timestamps must be timezone-aware and normalized consistently before comparison.

Source:
https://arxiv.org/abs/2103.11221

---

# 8. Paper 4 — Zoutendijk & Mitici — Probabilistic Flight Delay Predictions Using Machine Learning and Applications to the Flight-to-Gate Assignment Problem (2021)

This paper is particularly important for the SkyOps gate logic because it connects **delay uncertainty** directly to **gate conflicts**.

The study uses flight schedules and weather data at Rotterdam The Hague Airport, and compares Mixture Density Networks (MDN) and Random Forest regression (RFR) to estimate delay distributions.

## 8.1 Why probabilistic prediction matters

A point prediction says:

    expected delay = 25 min

A probabilistic prediction can say:

    delay distribution:
       10% chance around 5 min
       50% chance around 20 min
       90% chance below 45 min

This matters for gates because a gate may be free at the scheduled time but occupied later if a preceding aircraft is delayed.

## 8.2 Mixture Density Network theory

An MDN maps input features x_i to parameters of a mixture of Gaussian distributions.

For component j:

- alpha_j(x_i) = mixture weight;
- mu_j(x_i) = mean;
- sigma_j(x_i) = standard deviation.

The mixture density is:

    p(y_i | x_i) = sum_{j=1}^m alpha_j(x_i)
                   * phi_j(y_i | x_i)

with the Gaussian component:

    phi_j(y | x) =
       1/(sqrt(2*pi)*sigma_j)
       * exp(-(y-mu_j)^2/(2*sigma_j^2))

Mixture weights satisfy:

    sum_j alpha_j = 1

and standard deviations must satisfy:

    sigma_j > 0

A typical implementation uses softmax for alpha and an exponential/softplus-style transform for sigma.

The paper's training objective is negative log likelihood:

    E = - sum_i log( sum_j alpha_j(x_i) * phi_j(y_i | x_i) )

This is ML-training theory; the backend should never retrain the MDN.

## 8.3 Random Forest + KDE probabilistic output

A regular Random Forest regressor averages tree predictions for a point estimate.

The paper instead collects the tree outputs and applies Kernel Density Estimation (KDE) to construct a probability density.

Conceptually:

    KDE(y) = (1 / (n*h)) * sum_j K((y-y_j)/h)

where h is bandwidth and K is the kernel; the paper uses Gaussian kernels and a bandwidth of 1.5 in its experiment.

## 8.4 Prediction quality: CRPS

For a predicted CDF F(z) and actual delay y_bar, the paper defines:

    CRPS(F, y_bar)
      = integral from -infinity to +infinity of
        [F(z) - 1(z >= y_bar)]^2 dz

Lower CRPS is better because it penalizes both poorly calibrated and insufficiently sharp probability distributions.

Backend meaning:
If the ML component exposes a probabilistic model, keep the model distribution/quantiles/uncertainty metadata so downstream gate logic can use it. Do not invent a probability from a point estimate.

## 8.5 Deterministic flight-to-gate assignment formulation

Sets:

- N = aircraft/flight set.
- M = gate set.
- K = time-slot set.

Decision variable:

    x_ijt = 1 if aircraft i is assigned to gate j at time t,
            0 otherwise.

Presence indicator:

    s_it = 1 if aircraft i is scheduled to be at the airport
           at time slot t,
           0 otherwise.

Objective:

    minimize sum_i sum_j sum_t c_ij * x_ijt

Subject to:

    sum_j s_it * x_ijt = s_it
    for every i,t

This means a present aircraft must be assigned to exactly one gate.

Gate capacity constraint:

    sum_i s_it * x_ijt <= 1
    for every j,t

This prevents two aircraft from occupying the same gate in the same slot in the deterministic model.

Gate consistency constraint:

    s_it * x_ij(t+1) - s_i(t+1) * x_ijt = 0

This prevents the same aircraft from switching gates while it remains at the airport.

The paper uses a 24-hour horizon with 5-minute slots:

    24*60/5 = 288 slots.

## 8.6 Probabilistic gate constraint

Replace binary presence s_it with a probability p_it that aircraft i is present at time t.

The paper defines:

    f(p_it, r) = p_it / (r + p_it^2)

and uses the gate constraint:

    sum_i f(p_it,r) * p_it * x_ijt <= 1

where r is the permitted maximum overlap probability between aircraft assigned to the same gate and time slot.

This is the research formulation. Do not blindly implement the optimization solver in the backend unless explicitly requested.

## 8.7 Aircraft presence probability — the most important equation for SkyOps

Let:

    STA_i = scheduled arrival time
    STD_i = scheduled departure time
    y_arr_i = random arrival delay
    y_dep_i = random departure delay

Then:

    X_arr_i = STA_i + y_arr_i
    X_dep_i = STD_i + y_dep_i

Let F_Xarr_i(t) be the CDF of predicted arrival time and F_Xdep_i(t) the CDF of predicted departure time.

The aircraft-presence probability is:

    p_it = F_Xarr_i(t) * (1 - F_Xdep_i(t))

Interpretation:

    probability aircraft has arrived by t
    multiplied by
    probability aircraft has not yet departed by t.

This gives the probability that the aircraft is physically present at the airport/gate at time t.

For overnight aircraft the paper gives modified expressions based on only the appropriate arrival/departure CDF.

## 8.8 Practical adaptation for SkyOps

The clean backend design should support two modes:

MODE A — probabilistic predictor available:

- predictor returns an arrival/departure delay distribution or enough information to evaluate a CDF/quantiles;
- backend computes p_it using the above logic;
- backend uses p_it to estimate gate-conflict risk.

MODE B — current ML model only returns point estimates/probabilities:

- predictor returns expected delay minutes and a calibrated delayed probability;
- backend must not pretend it has the full delay CDF;
- use a deterministic/heuristic gate assignment based on predicted occupied intervals and a configurable safety buffer;
- expose the method as deterministic/heuristic rather than calling it the exact probabilistic FGAP from the paper.

This distinction is mandatory for scientific correctness.

Source:
https://www.mdpi.com/2226-4310/8/6/152

---

# 9. Paper 5 — Zhang & Klabjan — Optimization for Gate Re-Assignment (2017)

Journal:
Transportation Research Part B: Methodological.

Core problem:
A previously constructed gate plan can become infeasible or costly after adverse weather, delays, or cancellations.

The paper develops multi-commodity network-flow formulations and heuristic algorithms for fast gate reassignment.

## 9.1 Operational choices discussed

The framework considers options such as:

- reassign aircraft to an alternative gate;
- delay gate arrival while waiting for a gate;
- delay pushback while waiting for passengers;
- tow an aircraft to a parking area for long waits.

## 9.2 Objective concept

The paper minimizes a weighted combination of operational costs. A simplified conceptual representation is:

    minimize
        alpha * total_flight_delay
      + beta  * number_of_gate_reassignments
      + gamma * missed_passenger_connections
      + delta * passenger_transfer_distance

The exact formulation contains network-flow variables and additional constraints; this simplified equation is a design interpretation for SkyOps and is NOT a verbatim paper equation.

## 9.3 Important constraints for backend logic

At minimum a practical SkyOps gate recommendation must check:

1. Gate availability.
2. Time overlap.
3. Aircraft/gate compatibility.
4. Existing/committed assignments.
5. Whether a reassignment unnecessarily moves an aircraft already using a gate.
6. If passenger-connection data exists, whether moving gates increases transfer difficulty.

The paper emphasizes that the gate re-assignment problem is computationally difficult and uses specialized heuristics for response time.

## 9.4 SkyOps adaptation

Do not introduce CPLEX or a large MIP solver merely because the paper uses mathematical programming.

For the current practical application, implement a transparent, deterministic, conflict-aware heuristic first.

A suitable flow is:

    1. Get affected flight.
    2. Compute predicted occupied interval.
    3. Find compatible gates.
    4. Remove gates with hard conflicts.
    5. Compute a score for each remaining gate.
    6. Return the lowest-cost feasible candidate.

Use deterministic tie-breaking so the same input always gives the same recommendation.

Source:
https://www.sciencedirect.com/science/article/pii/S019126151630594X

---

# 10. Paper 6 — Pternea & Haghani — An Aircraft-to-Gate Reassignment Framework for Dealing with Schedule Disruptions (2019)

Journal:
Journal of Air Transport Management, 78, 116–132.

Core contribution:
A Binary Integer model for gate reassignment that explicitly considers passenger transfers, gate location, and the required connection time created by those gate locations.

## 10.1 Why gate location matters

A connecting passenger does not teleport from one gate to another.

Suppose:

    inbound flight arrives at Gate A
    outbound flight departs from Gate D

Available connection time alone is not enough. The walking/transfer time between A and D matters.

A simple operational feasibility rule is:

    available_connection_time >= required_connection_time(gate_A, gate_D)

If the inequality is false, the connection is at risk.

The paper's model uses binary assignment decisions and more detailed cost structures to capture this effect.

## 10.2 Binary decision concept

For a flight/aircraft i and gate k:

    x_ik = 1 if i is assigned to k
           0 otherwise

Typical assignment constraint:

    sum_k x_ik = 1

meaning each aircraft is assigned to one gate.

The paper's full formulation contains additional constraints and cost components; do not copy a reduced formula as if it were the exact paper formulation.

## 10.3 Missed connections

The paper's main practical point is that missed passenger connections can materially change the preferred gate assignment. Therefore the backend should keep the gate graph/location model extensible.

Recommended backend representation:

    gate_distance_minutes[gate_a][gate_b]

or a proper gate-coordinate representation from which walking/transfer time can later be derived.

If passenger connection information is unavailable in the current data, do not fabricate it. Disable that term and clearly state that the current recommender is aircraft/gate-centric rather than passenger-flow optimized.

## 10.4 Disruption scenarios

The paper studies disrupted schedules and uses stochastic delay scenarios, including examples involving normal and gamma-distributed delays. These distributions are research scenario inputs, not evidence that SkyOps should assume those exact distributions for live operations.

Backend rule:
Never hardcode a normal or gamma distribution simply because the paper used one for a scenario.

Source:
https://www.sciencedirect.com/science/article/pii/S0969699719300080

---

# 11. Paper 7 — Prasanna et al. — Smart Prediction of Weather-Induced Flight Delays Applying Deep Learning (2026)

This paper describes SkyPulse AI, an end-to-end web system using:

- XGBoost classifier;
- ANN classifier;
- soft voting;
- separate delay-duration regression;
- Flask web application;
- SQLite prediction history;
- dashboard analytics;
- SendGrid email notifications.

The paper reports a hybrid classification accuracy of 91.5% on its dataset, compared with 89.0% for XGBoost and 88.2% for ANN.

## 11.1 Input features

The dataset contains ten features:

- Airline
- Origin
- Destination
- Temperature
- Rain
- Visibility
- WindSpeed
- CloudCover
- Precipitation
- Scheduled departure time (CRSDepTime)

The paper uses preprocessing including categorical encoders, missing-value imputation, and scaling for the ANN path.

Backend implication:
Persist model-relevant input snapshots when storing a prediction so that an operator can understand what data generated the result.

## 11.2 Soft voting equation

The paper computes:

    P_final = (P_XGB + P_ANN) / 2

Then:

    if P_final > 0.5:
        classification = DELAYED
    else:
        classification = ON TIME

This is the paper's method, not SkyOps's current model requirement.

SkyOps currently intends to be model-agnostic and may use CatBoost. Therefore the backend should accept a predictor contract rather than hardcoding this XGBoost+ANN formula.

## 11.3 Delay-duration regression

A separate regression model predicts delay minutes only after the classifier predicts DELAYED.

Backend implication:
If the selected ML implementation follows this two-stage architecture, the prediction service should persist both:

    delayed_probability
    predicted_delay_minutes

Do not invent negative delay minutes for a delayed prediction, and do not convert a point prediction into a confidence interval without model support.

## 11.4 Practical limitation highlighted by the paper

The paper uses a static dataset and does not consume live flight/weather APIs. Its future-work discussion explicitly points toward live flight/weather integration and temporal models.

SkyOps's backend addresses the live-data integration aspect through external weather integration and a persistent operational database.

Source:
https://ijerst.org/index.php/ijerst/article/view/2452

---

# 12. What the research means for the SkyOps backend

The papers collectively suggest the following backend architecture:

    1. Store flight schedule and actual-operation data.
    2. Store aircraft identity and flight sequence information.
    3. Store airport/gate infrastructure.
    4. Retrieve weather for relevant location/time.
    5. Call an ML predictor.
    6. Persist the prediction and its input snapshot/model version.
    7. Propagate operational delay through aircraft rotations.
    8. Convert predicted timings into gate-occupancy intervals.
    9. Detect gate conflicts.
   10. Recommend a feasible gate.
   11. Persist recommendations/assignments for audit/history.
   12. Expose analytics over these records.

The backend must never confuse:

    ML prediction

with:

    operational decision.

Prediction says what may happen.
The backend operational layer decides what gates are feasible under the configured rules.

---

# 13. Backend data model

The target database should support at least these logical entities:

## airports

Suggested fields:

- id
- iata_code
- icao_code
- name
- city
- country
- latitude
- longitude
- timezone
- created_at

## gates

Suggested fields:

- id
- airport_id
- gate_code
- terminal
- latitude/longitude if available
- aircraft_size_limit or compatible categories
- active
- created_at

## flights

Suggested fields:

- id
- flight_number
- airline_code
- aircraft_id
- origin_airport_id
- destination_airport_id
- scheduled_departure
- scheduled_arrival
- actual_departure
- actual_arrival
- status
- cancelled
- diverted
- passenger_count if available
- block_time_minutes if available
- created_at
- updated_at

## weather

Suggested fields:

- id
- airport_id
- observed_at
- temperature_c
- precipitation_mm
- rain_mm
- visibility_km
- wind_speed_mps
- wind_direction_deg
- pressure_hpa
- cloud_cover_pct
- source
- raw_payload or provider metadata if justified

## predictions

Suggested fields:

- id
- flight_id
- generated_at
- model_name
- model_version
- delayed_probability
- predicted_delay_minutes
- arrival_delay_minutes if separately predicted
- departure_delay_minutes if separately predicted
- uncertainty metadata if supplied by the predictor
- input_snapshot JSON if justified
- status / prediction class

Never silently call an uncalibrated value a probability.

## gate_assignments

Suggested fields:

- id
- flight_id
- gate_id
- assignment_type (scheduled/recommended/reassigned/manual)
- score if applicable
- conflict_risk if applicable
- valid_from
- valid_to
- reason
- created_at

---

# 14. Time handling — extremely important

Aviation logic is highly time-sensitive.

Rules:

1. Store timestamps in UTC in the database where practical.
2. Use timezone-aware Python datetime objects.
3. Convert to the airport's local timezone only for display/business rules that explicitly require local time.
4. Never compare naive datetime objects from different sources.
5. Handle midnight/day rollover correctly.
6. Never represent HHMM such as 2355 as the integer 2355 and then perform arithmetic directly on that integer.

Correct:

    23:55 + 10 minutes = next day 00:05

Incorrect:

    2355 + 10 = 2365

Create small, well-tested time utilities for minute arithmetic when needed.

---

# 15. Delay propagation logic

The research repeatedly emphasizes delay propagation.

SkyOps needs to identify an aircraft's subsequent flight.

Basic relationship:

    Flight A arrival
          |
          | same aircraft
          v
    Flight B departure

Let:

    actual_or_predicted_arrival_A
    required_turnaround_B
    scheduled_departure_B

A simple minimum feasible departure is:

    earliest_departure_B = arrival_time_A + turnaround_time_B

Therefore propagated delay can be represented as:

    propagated_delay_B =
        max(0,
            earliest_departure_B - scheduled_departure_B)

If Flight B already has an independent predicted/root delay, combine the mechanisms carefully rather than double-counting them.

A safe starting rule is:

    final_departure_delay_B =
        max(independent_predicted_delay_B,
            propagated_aircraft_delay_B)

Do not add the two blindly unless the model explicitly says they are independent additive components.

The system must preserve the distinction between:

- root/independent predicted delay;
- inherited aircraft-rotation delay;
- weather/event delay;
- final operational estimated delay.

This prevents double counting.

---

# 16. Turnaround logic

A turnaround pairs an arriving flight to the next departure operated by the same aircraft.

Do not pair solely by airline or flight number.

Recommended matching keys:

- aircraft_id;
- airport where the aircraft is turning;
- chronological consistency.

For each arrival A, find the earliest subsequent departure B for the same aircraft at the same airport such that:

    departure_B_time > arrival_A_time

and optionally:

    departure_B_time - arrival_A_time >= configured_minimum_turnaround

The minimum turnaround is an operational configuration, not a universal constant.

Never infer an exact turnaround time from a paper unless the application's configuration explicitly adopts it.

---

# 17. Gate presence and occupied intervals

For a deterministic version, define:

    occupied_start_i = predicted/scheduled arrival time
    occupied_end_i   = predicted/scheduled departure time

Then the flight occupies a gate over:

    [occupied_start_i, occupied_end_i)

Use a half-open interval so that:

    previous flight ends at 10:30
    next flight starts at 10:30

does not create an artificial overlap.

For 5-minute discretization inspired by Zoutendijk & Mitici:

    slot_index = floor(minutes_since_horizon_start / 5)

Do not create 5-minute floating-point timestamps when ordinary interval overlap is sufficient. Keep exact datetimes and derive slots only when the algorithm needs them.

---

# 18. Gate conflict detection

Two assignments conflict when their gate-occupancy intervals overlap:

    max(start_A, start_B) < min(end_A, end_B)

If true, they cannot share the same gate under the deterministic model.

If a safety buffer B is required:

    expanded_start = start - B_before
    expanded_end   = end + B_after

Then apply the same overlap test.

Do not hide the buffer inside random constants. Store it in configuration.

---

# 19. Gate recommendation algorithm for the practical SkyOps version

Unless a full mathematical-programming solver is explicitly requested, use a deterministic conflict-aware heuristic.

Recommended process:

### Step 1 — identify the flight

Load:

- schedule;
- current status;
- predicted delay(s);
- aircraft requirements;
- airport;
- current gate if any;
- relevant turnaround/connection information.

### Step 2 — calculate predicted occupancy

Use the best available timing information in this order:

1. actual known time, if already occurred;
2. operationally updated time, if available;
3. ML-predicted time;
4. scheduled time as fallback.

Never overwrite actual history with a prediction.

### Step 3 — build candidate gates

Remove gates that are:

- inactive;
- at another airport;
- incompatible with aircraft requirements;
- closed/blocked;
- conflicting with an existing assignment.

### Step 4 — calculate gate score

Use configurable weighted terms, for example:

    score(g) =
        w_distance       * normalized_distance_cost
      + w_conflict       * conflict_penalty
      + w_reassignment   * reassignment_penalty
      + w_connection     * connection_penalty
      + w_preference     * preference_penalty

This is a SkyOps engineering formulation, not a claim that this exact equation appears in any of the papers.

### Step 5 — deterministic tie-break

If two gates have the same score, use a stable tie-break such as:

    lower gate_code / lower gate_id

Never use random choice.

### Step 6 — save an auditable recommendation

Persist:

- flight;
- recommended gate;
- score;
- generation time;
- prediction/model version;
- reason;
- conflict-risk information.

---

# 20. Nearest-gate logic

"Nearest" must have a defined meaning.

Possible meanings:

1. Physical coordinate distance.
2. Passenger walking distance.
3. Taxiway distance.
4. Static preference ranking.

For the current backend, if only gate coordinates are available, Haversine/geographic distance may be used as a proxy. Document it as a proxy rather than claiming it equals real walking distance.

For two coordinates:

    Haversine distance =
        2r * asin(sqrt(sin^2(Delta_phi/2)
        + cos(phi_1)cos(phi_2)sin^2(Delta_lambda/2)))

But if airport-internal walking distances are available, use those instead of geographic great-circle distance.

---

# 21. Prediction integration contract

The backend should be model-agnostic.

Maintain a predictor interface such as:

```python
class DelayPredictor(Protocol):
    def predict(self, features: Mapping[str, Any]) -> DelayPrediction:
        ...
```

The backend must not import CatBoost training code into services.

## Recommended prediction response contract

At minimum:

```json
{
  "model_name": "catboost",
  "model_version": "...",
  "delayed_probability": 0.82,
  "predicted_delay_minutes": 25,
  "prediction_class": "DELAYED",
  "generated_at": "..."
}
```

Optional probabilistic fields may include:

```json
{
  "arrival_delay_distribution": {...},
  "departure_delay_distribution": {...},
  "p50_delay_minutes": 20,
  "p80_delay_minutes": 38,
  "p90_delay_minutes": 52,
  "delay_std_minutes": 14
}
```

Only include these optional fields when the model genuinely provides them.

Do not derive p80/p90/std from a single expected-delay number.

## Why the distinction matters

A point prediction:

    E[Y] = 25 minutes

is not enough to compute:

    P(Y <= t)

unless a distributional assumption/model is available.

Therefore the backend must never fabricate a CDF merely to claim compliance with the probabilistic gate-assignment research.

---

# 22. Weather integration

Primary weather integration planned for backend:

    Open-Meteo adapter

The backend should:

1. determine the relevant airport/location;
2. determine the relevant time window;
3. request weather data;
4. normalize units;
5. validate the response;
6. cache/store useful observations where appropriate;
7. expose the weather through a clean internal interface.

Possible useful variables from the research include:

- temperature;
- precipitation/rain;
- visibility;
- wind speed/direction;
- pressure;
- cloud cover;
- humidity;
- ceiling/sky conditions if available.

Do not pass provider-specific JSON throughout the application. Normalize it through a weather schema/domain object.

Keep the provider name and observation timestamp.

If weather data is unavailable:

- do not crash the entire flight service unnecessarily;
- return an explicit missing-data state;
- allow the predictor adapter/fallback strategy to decide whether prediction is possible.

---

# 23. API design

Planned endpoint families:

    /api/v1/health
    /api/v1/airports
    /api/v1/flights
    /api/v1/predictions
    /api/v1/gates
    /api/v1/weather
    /api/v1/analytics

Keep request/response models in Pydantic schemas.

Do not return raw ORM objects directly.

Use stable response models.

Use correct HTTP status codes.

Validate IDs and enums.

Return structured errors.

Never leak stack traces or secrets to API clients.

---

# 24. Prediction API execution flow

Expected high-level flow:

    POST /predictions
          |
          v
    validate flight ID/request
          |
          v
    load flight + related airport data
          |
          v
    obtain weather if required
          |
          v
    assemble prediction feature snapshot
          |
          v
    predictor.predict(...)
          |
          v
    validate predictor output
          |
          v
    persist Prediction record
          |
          v
    return stable API response

The input snapshot should make debugging possible.

If the model service fails, return a meaningful application error and do not create a fake prediction.

---

# 25. Gate recommendation execution flow

Expected high-level flow:

    request flight gate recommendation
          |
          v
    load flight
          |
          v
    load gates + existing assignments
          |
          v
    obtain best available predicted timing
          |
          v
    calculate occupied interval
          |
          v
    filter incompatible/closed/conflicting gates
          |
          v
    score remaining candidates
          |
          v
    deterministic tie-break
          |
          v
    return recommendation

If no gate is feasible:

    return a structured no-feasible-gate result

Do not simply choose a conflicting gate because a list is non-empty.

---

# 26. Delay-propagation execution flow

Expected flow:

    flight A has delay
          |
          v
    find next flight B using same aircraft
          |
          v
    identify turnaround requirement
          |
          v
    calculate earliest feasible operation of B
          |
          v
    compare with scheduled B time
          |
          v
    store inherited/propagated delay

Propagate through the rotation iteratively only while:

- the same aircraft relationship is valid;
- chronological ordering is valid;
- the next flight exists;
- the propagation should not cross a maintenance/repositioning event incorrectly.

Never create an infinite loop.

Track visited flight IDs in graph-like traversals.

---

# 27. Analytics

Analytics endpoints should aggregate persisted operational data rather than re-running ML training or expensive gate optimization.

Useful backend analytics include:

- flights by status;
- average predicted delay;
- average actual delay where actuals exist;
- delayed-flight count;
- prediction count;
- gate utilization;
- gate conflicts;
- reassignments;
- propagated delays;
- weather observations linked to predictions.

Always distinguish:

    predicted metrics

from:

    actual metrics.

Never call a prediction an actual outcome.

---

# 28. Authentication and authorization

The existing design mentions Supabase JWT authentication and operator-role authorization.

Backend rules:

- validate JWT correctly;
- do not trust role values sent in request bodies;
- extract identity/role from verified authentication context;
- protect operator-only actions;
- do not log raw access tokens;
- never place secrets in source code;
- keep Supabase/service credentials in environment variables.

---

# 29. Database and repository rules

Repositories own SQL/database access.

Services should not contain raw SQL unless the existing architecture explicitly requires it.

Use transactions for multi-step writes that must remain consistent.

For example, if saving a new gate assignment and invalidating a prior active recommendation are logically atomic, use one transaction.

Add indexes for frequent query paths such as:

- airport_id;
- flight dates/times;
- aircraft_id;
- gate_id;
- assignment validity interval;
- weather observation timestamp.

Do not add indexes blindly. Check query patterns first.

---

# 30. Data consistency rules

The same real-world event must not be represented inconsistently across tables.

Examples:

- airport code should map to one airport ID;
- a gate must belong to one airport;
- a flight's origin/destination must reference valid airports;
- a gate assignment must reference a valid flight/gate pair;
- a prediction must reference the flight it predicts;
- actual times must remain historical facts;
- predictions must remain predictions.

Use foreign keys and validation where appropriate.

---

# 31. Edge cases Gemini must explicitly handle

Before declaring a feature complete, consider:

- missing weather;
- missing aircraft ID;
- cancelled flight;
- diverted flight;
- no subsequent aircraft rotation;
- midnight crossing;
- overnight aircraft;
- multiple candidate gates;
- no compatible gate;
- two flights with touching but non-overlapping intervals;
- same flight requested repeatedly;
- stale prediction;
- stale gate assignment;
- duplicate flight identifiers from external data;
- invalid timestamps;
- timezone mismatch;
- ML service unavailable;
- invalid predictor probability outside [0,1];
- negative predicted delay where the contract does not permit it;
- database transaction failure;
- concurrent gate-assignment requests.

Do not use silent fallbacks that create an operationally false answer.

---

# 32. Determinism and reproducibility

Backend algorithms should be deterministic unless there is a strong reason otherwise.

For the same database state, configuration, and prediction input:

    same request -> same recommendation

Use stable sorting and deterministic tie-breaks.

Record model version/configuration with prediction and recommendation records.

---

# 33. Testing requirements

Every important domain algorithm needs unit tests.

At minimum test:

## Delay propagation

- no delay;
- one propagated delay;
- multiple sequential flights;
- independent predicted delay versus inherited delay;
- midnight rollover;
- missing next flight.

## Gate conflict

- obvious overlap;
- touching intervals;
- nested interval;
- no overlap;
- buffer expansion.

## Gate assignment

- one free gate;
- multiple gates;
- incompatible gate;
- conflicting gate;
- no feasible gate;
- deterministic tie-break;
- reassigning an existing flight.

## Predictor adapter

- valid output;
- probability < 0;
- probability > 1;
- missing required fields;
- model unavailable;
- stale model version if relevant.

## Weather adapter

- valid response;
- missing variable;
- timeout;
- malformed provider response;
- timezone conversion.

## API contract

- correct status codes;
- schema validation;
- auth failures;
- authorization failures;
- not-found cases.

---

# 34. Error handling principles

Use typed application exceptions.

Examples:

- FlightNotFoundError
- GateNotFoundError
- NoFeasibleGateError
- PredictorUnavailableError
- InvalidPredictionError
- WeatherProviderError
- UnauthorizedOperatorError

Translate these into stable API errors.

Do not expose implementation details such as SQL statements, stack traces, API keys, or provider credentials.

---

# 35. Research-to-code mapping

Research concept -> backend implementation:

    delay = actual - scheduled
        -> flight/time utilities

    temporal/spatial/weather/state features
        -> database schemas + weather integration + feature snapshot builder

    delay propagation
        -> domain/propagation.py

    aircraft rotation
        -> domain/turnarounds.py

    aircraft presence probability
        -> domain/presence.py

    deterministic FGAP
        -> domain/gate_assignment.py or service layer

    probabilistic FGAP concept
        -> optional extension when probabilistic predictor output exists

    gate location / connection time
        -> gate metadata + optional gate-to-gate transfer-time matrix

    real-time weather integration
        -> integrations/weather.py

    prediction contract
        -> domain/ports.py + integrations/predictor.py

    prediction persistence
        -> db models + repository

    operational recommendation
        -> services/gate_recommendation.py

---

# 36. What NOT to do

Never:

- train CatBoost from a FastAPI request;
- fit an ML model every time /predictions is called;
- fabricate probabilities from expected delay minutes;
- call the heuristic a mathematical optimum without a proof/solver;
- use random gate selection;
- silently ignore gate conflicts;
- treat scheduled time as actual time;
- mix local and UTC times without conversion;
- use HHMM integers for time arithmetic;
- overwrite actual flight history with predicted values;
- double-count propagated delay and independent delay without a defined rule;
- add passenger-connection penalties when passenger data does not exist;
- use gate coordinate distance as "walking distance" unless it is explicitly documented as a proxy;
- introduce a large optimization solver when the current project only requires a practical heuristic;
- rewrite the project architecture unnecessarily;
- create duplicate database models/repositories/services;
- hardcode API keys, passwords, JWT secrets, or Supabase service-role keys;
- switch Git branches automatically;
- commit or push automatically unless explicitly instructed.

---

# 37. Existing backend tree from the project specification

The original planned structure was:

```text
skyops-backend/
├── app/
│   ├── main.py                 app factory, CORS, error handling
│   ├── api/                    routing, auth (Supabase JWT, operator role), validation only
│   │   └── v1/endpoints/       health, airports, flights, predictions, gates, weather, analytics
│   ├── schemas/                Pydantic request/response models
│   ├── services/               use cases (prediction, gate recommendation, weather, analytics)
│   ├── domain/                 pure logic, no DB or framework imports
│   │   ├── ports.py            DelayPredictor interface
│   │   ├── presence.py         gate-presence probability per 5-minute slot
│   │   ├── gate_assignment.py  conflict-aware gate assignment
│   │   ├── propagation.py      knock-on delay along an aircraft's rotation
│   │   └── turnarounds.py      pair arrival with aircraft's next departure
│   ├── repositories/           all SQL
│   ├── db/                     ORM models
│   ├── integrations/           Open-Meteo adapter, predictor factory + rule-based stub
│   └── core/                   settings, logging, exceptions
├── alembic/                    migrations
├── scripts/seed_db.py
├── tests/
├── docs/
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── .env.example
├── pyproject.toml
└── README.md
```

Preserve this architecture unless a concrete implementation need requires change.

---

# 38. Required domain-module behavior

## app/domain/presence.py

Responsibilities:

- deterministic gate presence from intervals;
- optional probabilistic presence when a genuine delay distribution/CDF exists;
- 5-minute slot conversion when required;
- no database imports;
- no FastAPI imports.

## app/domain/gate_assignment.py

Responsibilities:

- hard-constraint filtering;
- overlap/conflict detection;
- compatibility filtering;
- candidate scoring;
- stable tie-breaking;
- optional robustness/risk penalty.

## app/domain/propagation.py

Responsibilities:

- build aircraft rotation chains from prepared domain objects;
- propagate inherited operational delay;
- prevent cycles;
- preserve root versus inherited delay.

## app/domain/turnarounds.py

Responsibilities:

- identify next departure by aircraft and airport;
- enforce chronology;
- calculate available turnaround time;
- return explicit no-match when no next leg exists.

## app/domain/ports.py

Responsibilities:

- define interfaces for predictor/weather/repositories where the architecture uses ports;
- remain framework independent.

---

# 39. Recommended service responsibilities

## prediction.py

Coordinates:

    flight load
    + weather load
    + feature snapshot construction
    + predictor call
    + output validation
    + persistence

It must not contain CatBoost training code.

## weather.py

Coordinates:

    airport/location
    + timestamp
    + provider adapter
    + normalization
    + caching/persistence if needed

## gate_recommendation.py

Coordinates:

    flight state
    + prediction
    + gates
    + existing assignments
    + domain assignment engine
    + persistence/audit

## analytics.py

Coordinates aggregate read-only operational metrics.

---

# 40. Backend implementation order

When building or repairing the project, use this order unless the existing repository requires a different sequence:

1. Inspect existing code and migrations.
2. Verify configuration/environment handling.
3. Verify database models and repositories.
4. Verify basic flight/airport/gate CRUD/read APIs.
5. Verify weather integration.
6. Verify predictor contract and stub.
7. Implement prediction persistence.
8. Implement turnaround pairing.
9. Implement delay propagation.
10. Implement deterministic gate conflict/assignment logic.
11. Add optional probabilistic presence support if the predictor provides a true distribution.
12. Implement recommendation/reassignment APIs.
13. Add analytics endpoints.
14. Add tests.
15. Run lint/type checks/tests/migration checks.
16. Only then optimize/refactor.

---

# 41. Gemini CLI operating procedure

Whenever asked to modify the backend:

### Before coding

1. Inspect relevant files.
2. Inspect related tests.
3. Inspect database models/migrations if data is involved.
4. Search for an existing implementation before creating a new one.
5. Check whether the requested behavior belongs to API, service, domain, repository, or integration layer.

### During coding

- make the smallest coherent change;
- preserve current public API unless change is required;
- preserve existing variable/model names where reasonable;
- avoid unnecessary dependencies;
- validate all external/model input;
- keep pure logic pure;
- keep SQL in repositories;
- keep external provider details behind adapters.

### After coding

Run appropriate checks.
At minimum when practical:

```text
pytest
ruff check .
```

If the repository uses other configured checks, run them too.

Then report:

- files changed;
- behavior implemented;
- tests/checks run;
- any assumptions;
- any remaining limitations.

Do not claim a feature is complete if a required dependency/model/API is still a stub.

---

# 42. Scientific correctness rules

The backend may implement simplified engineering heuristics, but it must clearly distinguish them from research formulations.

Use wording such as:

    research-inspired heuristic
    deterministic approximation
    operational proxy
    simplified implementation

Do not write:

    "optimal"
    "mathematically guaranteed"
    "probabilistically robust"

unless the actual implementation and assumptions support those claims.

Most importantly:

    a point estimate is not a probability distribution;
    a heuristic is not an optimizer;
    a coordinate distance is not automatically a walking distance;
    a prediction is not an observed fact.

---

# 43. Final end-to-end behavior expected from the backend

A valid request should be able to follow this logical chain:

    1. Identify a flight.
    2. Load its current/historical operational context.
    3. Load weather relevant to its location/time.
    4. Ask the predictor for a prediction through the predictor interface.
    5. Validate and persist that prediction.
    6. Identify the aircraft's next rotation when applicable.
    7. Propagate delay only when the aircraft relationship and turnaround logic justify it.
    8. Calculate predicted/known gate occupancy intervals.
    9. Determine candidate gates.
   10. Reject hard conflicts and incompatibilities.
   11. Score remaining gates deterministically.
   12. Return a recommendation with a reason and audit information.
   13. Persist the recommendation if requested by the business operation.
   14. Expose historical/aggregate analytics separately.

Every stage must have explicit data validation and failure behavior.

---

# 44. Important current-model note

The research includes Random Forest, MDN, LSTM, XGBoost, and ANN approaches.

The current SkyOps implementation may use **CatBoost** for the ML component.

Therefore:

- do not force the backend to implement the research models directly;
- do not replace CatBoost with another model because a paper used another model;
- keep the backend predictor contract model-agnostic;
- store model_name/model_version with predictions;
- keep the domain logic independent of the ML framework.

The research informs the **data and operational logic**. The selected production/demo model is an implementation decision made outside the backend training layer.

---

# 45. References used for this backend context

1. Sternberg, Soares, Carvalho, Ogasawara, *A Review on Flight Delay Prediction* (2017 preprint; later systematic-review publication).
   https://arxiv.org/abs/1703.06118

2. Huo, Keung, Lee, Ng, Li, *The Prediction of Flight Delay: Big Data-Driven Machine Learning Approach* (2020).
   https://ira.lib.polyu.edu.hk/handle/10397/89846

3. Zhang, Jiang, Liu, Song, *Spatio-Temporal Data Mining for Aviation Delay Prediction* (2021).
   https://arxiv.org/abs/2103.11221

4. Zoutendijk & Mitici, *Probabilistic Flight Delay Predictions Using Machine Learning and Applications to the Flight-to-Gate Assignment Problem* (2021).
   https://doi.org/10.3390/aerospace8060152

5. Zhang & Klabjan, *Optimization for Gate Re-Assignment* (2017).
   https://doi.org/10.1016/j.trb.2016.11.006

6. Pternea & Haghani, *An Aircraft-to-Gate Reassignment Framework for Dealing with Schedule Disruptions* (2019).
   https://doi.org/10.1016/j.jairtraman.2019.01.005

7. Prasanna et al., *Smart Prediction of Weather-Induced Flight Delays Applying Deep Learning* (2026).
   https://doi.org/10.62643/ijerst.2026.v22.n2(1).pp61-65

---

# 46. Final instruction to Gemini

You are working on the **SkyOps backend**.

Do not blindly code from the project title. First understand the existing repository and the research-grounded operational rules above.

When a request touches prediction, gates, propagation, weather, or time, check the relevant research section and then translate it into a practical backend implementation without claiming stronger mathematical guarantees than the code actually provides.

Prefer correct, explainable, deterministic backend behavior over unnecessary complexity.

Do not modify unrelated work.

Do not train ML models inside the backend.

Do not fabricate missing data.

Do not silently ignore conflicts or validation failures.

Do not declare a recommendation feasible unless the hard constraints are actually satisfied.
