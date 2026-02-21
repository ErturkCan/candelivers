# CanDelivers - Last-Mile Logistics for Bulky Items

Last-mile logistics optimization platform for bulky item delivery in dense urban environments. Routing optimization, constraint modeling, and operational simulation for local delivery coordination. Built on the [PARM](https://github.com/ErturkCan/parm) shared intelligence layer.

## Features

- **VRPTW Solver**: Vehicle Routing Problem with Time Windows using nearest-neighbor heuristic + 2-opt improvement
- **Constraint Engine**: Vehicle capacity, time windows, driver hours, zone restrictions
- **Delivery Simulation**: Monte Carlo simulation of delivery scenarios with traffic modeling
- **Route Optimization**: Multi-objective optimization balancing time, cost, and customer satisfaction
- **PARM Integration**: Uses PARM's agent orchestration for dynamic route replanning
- **Real-Time Tracking**: Event-driven delivery status updates via PARM workflow engine

## Architecture

```
CanDelivers (Python)
├── candelivers/
│   ├── routing/        # VRPTW solver, nearest-neighbor, 2-opt
│   ├── constraints/    # Vehicle capacity, time windows, zones
│   ├── simulation/     # Monte Carlo delivery simulation
│   ├── models/         # Domain models (Order, Vehicle, Route)
│   └── parm_connector/ # PARM platform integration
├── tests/              # Comprehensive test suite
├── config/             # Simulation configurations
└── scripts/            # CLI tools and utilities
```

### PARM Integration

CanDelivers uses PARM's infrastructure for:
- **Agent Orchestration**: Route planning agents coordinated via PARM
- **Workflow Automation**: Order intake -> route planning -> dispatch -> tracking
- **Context Pipeline**: Real-time traffic and delivery context processing
- **Decision Engine**: Dynamic replanning when deliveries are delayed

## Core Algorithm

### VRPTW Solver

1. **Construction Phase**: Nearest-neighbor heuristic builds initial routes
2. **Improvement Phase**: 2-opt local search reduces total distance
3. **Constraint Validation**: Each route checked against time windows, capacity, driver hours
4. **Scoring**: Multi-objective score combining distance, time window violations, vehicle utilization

### Simulation Engine

Monte Carlo simulation with configurable parameters:
- Traffic delay distributions (lognormal)
- Service time variability
- Order volume patterns
- Vehicle breakdown probability

## Usage

```bash
# Install
pip install -e .

# Run route optimization
python -m candelivers.cli optimize --orders orders.json --vehicles 3

# Run simulation
python -m candelivers.cli simulate --config config/urban_dense.json --runs 1000

# Run tests
pytest tests/ -v
```

## Configuration

```json
{
  "area": {
    "center": [52.3676, 4.9041],
    "radius_km": 15
  },
  "vehicles": {
    "count": 5,
    "capacity_kg": 500,
    "max_hours": 8
  },
  "simulation": {
    "runs": 1000,
    "traffic_model": "lognormal",
    "service_time_mean_min": 15
  }
}
```

## Tech Stack

- **Language**: Python 3.11+
- **Optimization**: Custom VRPTW solver (no heavy dependencies)
- **Simulation**: NumPy for Monte Carlo
- **Testing**: pytest with 90%+ coverage
- **Platform**: PARM shared intelligence layer

## License

MIT License - See LICENSE file
