# Vividly Topic Hierarchy

**Version:** 1.0 (MVP)
**Last Updated:** October 27, 2025
**Target Audience:** High School STEM (Grades 9-12)

## Table of Contents

1. [Overview](#overview)
2. [Hierarchy Structure](#hierarchy-structure)
3. [Physics Topics](#physics-topics)
4. [Mathematics Topics](#mathematics-topics)
5. [Topic Metadata](#topic-metadata)
6. [Topic ID Naming Convention](#topic-id-naming-convention)
7. [Content Alignment](#content-alignment)

---

## Overview

The Vividly topic hierarchy organizes High School STEM content in a structured, standards-aligned format. Each topic represents a discrete learning objective that can be explained in a 2-4 minute micro-lesson.

### Design Principles

1. **Granular**: Each leaf topic = one concept (teachable in <5 minutes)
2. **Hierarchical**: Topics organized by subject → unit → concept → subtopic
3. **Standards-Aligned**: Mapped to Common Core and NGSS where applicable
4. **Prerequisite-Aware**: Topics reference required prior knowledge
5. **Grade-Banded**: Difficulty calibrated for specific grade levels

### MVP Scope

For the MNPS pilot, we focus on:
- **Physics**: Mechanics, Energy, Waves
- **Mathematics**: Algebra I & II, Geometry, Pre-Calculus

**Total Topics**: ~240 (120 Physics, 120 Math)

---

## Hierarchy Structure

```
Subject (Level 0)
  └─ Unit (Level 1)
      └─ Concept (Level 2)
          └─ Topic (Level 3)
              └─ Subtopic (Level 4)
```

### Example: Newton's Third Law

```
Physics                                    [Level 0]
  └─ Mechanics                              [Level 1]
      └─ Newton's Laws of Motion             [Level 2]
          └─ Newton's Third Law              [Level 3]
              ├─ Action-Reaction Pairs       [Level 4]
              ├─ Force Magnitude             [Level 4]
              └─ Common Misconceptions       [Level 4]
```

---

## Physics Topics

### 1. Mechanics (topic_phys_mech)

#### 1.1 Kinematics (topic_phys_mech_kinem)

**Grade Level**: 9-10

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_phys_mech_kinem_position` | Position and Displacement | Understanding position vectors and displacement | None |
| `topic_phys_mech_kinem_velocity` | Velocity and Speed | Difference between velocity and speed | Position |
| `topic_phys_mech_kinem_accel` | Acceleration | Rate of change of velocity | Velocity |
| `topic_phys_mech_kinem_graphs` | Motion Graphs | Position, velocity, acceleration graphs | Accel |
| `topic_phys_mech_kinem_freefall` | Free Fall | Objects under gravity alone | Accel |
| `topic_phys_mech_kinem_projectile` | Projectile Motion | 2D motion under gravity | Free Fall |

#### 1.2 Forces (topic_phys_mech_forces)

**Grade Level**: 9-10

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_phys_mech_forces_intro` | What is a Force? | Definition and units of force | None |
| `topic_phys_mech_forces_friction` | Friction Forces | Static and kinetic friction | Forces Intro |
| `topic_phys_mech_forces_normal` | Normal Force | Contact forces perpendicular to surface | Forces Intro |
| `topic_phys_mech_forces_tension` | Tension Forces | Forces in ropes and strings | Forces Intro |
| `topic_phys_mech_forces_gravity` | Gravitational Force | Weight and gravity | Forces Intro |
| `topic_phys_mech_forces_net` | Net Force | Vector sum of all forces | Forces Intro |

#### 1.3 Newton's Laws (topic_phys_mech_newton)

**Grade Level**: 9-10

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_phys_mech_newton_1` | Newton's First Law | Inertia and equilibrium | Net Force |
| `topic_phys_mech_newton_1_inertia` | Inertia Examples | Real-world inertia situations | Newton 1 |
| `topic_phys_mech_newton_2` | Newton's Second Law | F = ma and applications | Newton 1 |
| `topic_phys_mech_newton_2_mass` | Mass and Acceleration | Relationship between m and a | Newton 2 |
| `topic_phys_mech_newton_3` | Newton's Third Law | Action-reaction pairs | Newton 2 |
| `topic_phys_mech_newton_3_pairs` | Identifying Action-Reaction | Finding paired forces | Newton 3 |
| `topic_phys_mech_newton_3_magnitude` | Force Magnitude in Pairs | Equal and opposite forces | Newton 3 |

#### 1.4 Circular Motion (topic_phys_mech_circular)

**Grade Level**: 10-11

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_phys_mech_circular_centripetal` | Centripetal Acceleration | Acceleration toward center | Accel, Velocity |
| `topic_phys_mech_circular_force` | Centripetal Force | Force causing circular motion | Centripetal Accel |
| `topic_phys_mech_circular_period` | Period and Frequency | Time for one revolution | Circular Motion |
| `topic_phys_mech_circular_gravity` | Orbital Motion | Circular orbits under gravity | Gravity, Centripetal |

### 2. Energy (topic_phys_energy)

#### 2.1 Work and Energy (topic_phys_energy_work)

**Grade Level**: 10-11

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_phys_energy_work_def` | Definition of Work | W = F·d and units | Forces |
| `topic_phys_energy_work_angle` | Work and Angle | Work with angled forces | Work Def |
| `topic_phys_energy_ke` | Kinetic Energy | Energy of motion KE = ½mv² | Work |
| `topic_phys_energy_pe_grav` | Gravitational Potential Energy | PE = mgh | Work, Gravity |
| `topic_phys_energy_pe_elastic` | Elastic Potential Energy | Energy in springs | Work |
| `topic_phys_energy_conservation` | Conservation of Energy | Energy transformation | KE, PE |
| `topic_phys_energy_power` | Power | Rate of energy transfer | Work |

#### 2.2 Momentum (topic_phys_energy_momentum)

**Grade Level**: 10-11

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_phys_energy_momentum_def` | Momentum | p = mv and impulse | Velocity |
| `topic_phys_energy_momentum_impulse` | Impulse-Momentum Theorem | Δp = FΔt | Momentum |
| `topic_phys_energy_momentum_conservation` | Conservation of Momentum | Isolated system momentum | Momentum |
| `topic_phys_energy_momentum_collisions` | Elastic Collisions | Collisions conserving KE | Conservation |
| `topic_phys_energy_momentum_inelastic` | Inelastic Collisions | Collisions losing KE | Conservation |

### 3. Waves and Sound (topic_phys_waves)

**Grade Level**: 11-12

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_phys_waves_intro` | What is a Wave? | Wave properties and types | None |
| `topic_phys_waves_transverse` | Transverse Waves | Perpendicular oscillation | Waves Intro |
| `topic_phys_waves_longitudinal` | Longitudinal Waves | Parallel oscillation | Waves Intro |
| `topic_phys_waves_velocity` | Wave Velocity | v = fλ relationship | Waves Intro |
| `topic_phys_waves_sound_speed` | Speed of Sound | Sound wave propagation | Wave Velocity |
| `topic_phys_waves_doppler` | Doppler Effect | Frequency shift in motion | Sound Speed |

### 4. Electricity (topic_phys_elec) - Future Phase

*(To be developed post-MVP)*

---

## Mathematics Topics

### 1. Algebra I (topic_math_alg1)

#### 1.1 Linear Equations (topic_math_alg1_linear)

**Grade Level**: 9

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_math_alg1_linear_solve` | Solving Linear Equations | One-variable equations | Arithmetic |
| `topic_math_alg1_linear_graph` | Graphing Linear Equations | Plotting y = mx + b | Coordinate Plane |
| `topic_math_alg1_linear_slope` | Slope | Rate of change | Graphing |
| `topic_math_alg1_linear_intercept` | Y-Intercept | Where line crosses y-axis | Graphing |
| `topic_math_alg1_linear_parallel` | Parallel Lines | Equal slopes | Slope |
| `topic_math_alg1_linear_perpendicular` | Perpendicular Lines | Negative reciprocal slopes | Slope |

#### 1.2 Systems of Equations (topic_math_alg1_systems)

**Grade Level**: 9

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_math_alg1_systems_graphing` | Solving by Graphing | Finding intersection point | Linear Graph |
| `topic_math_alg1_systems_substitution` | Substitution Method | Algebraic substitution | Solving Linear |
| `topic_math_alg1_systems_elimination` | Elimination Method | Adding/subtracting equations | Substitution |
| `topic_math_alg1_systems_applications` | Application Problems | Real-world systems | Elimination |

#### 1.3 Polynomials (topic_math_alg1_poly)

**Grade Level**: 9-10

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_math_alg1_poly_add` | Adding Polynomials | Combining like terms | Arithmetic |
| `topic_math_alg1_poly_multiply` | Multiplying Polynomials | Distribution and FOIL | Adding |
| `topic_math_alg1_poly_factor_gcf` | Factoring GCF | Greatest common factor | Multiply |
| `topic_math_alg1_poly_factor_trinomial` | Factoring Trinomials | ax² + bx + c | GCF |

### 2. Algebra II (topic_math_alg2)

#### 2.1 Quadratic Functions (topic_math_alg2_quad)

**Grade Level**: 10-11

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_math_alg2_quad_standard` | Standard Form | y = ax² + bx + c | Polynomials |
| `topic_math_alg2_quad_vertex` | Vertex Form | y = a(x-h)² + k | Standard Form |
| `topic_math_alg2_quad_graph` | Graphing Parabolas | Shape and transformations | Vertex Form |
| `topic_math_alg2_quad_solve_factor` | Solving by Factoring | Finding zeros | Factoring |
| `topic_math_alg2_quad_solve_formula` | Quadratic Formula | x = [-b±√(b²-4ac)]/2a | Solving Factor |
| `topic_math_alg2_quad_discriminant` | The Discriminant | b² - 4ac and solutions | Quad Formula |

#### 2.2 Exponential Functions (topic_math_alg2_exp)

**Grade Level**: 10-11

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_math_alg2_exp_growth` | Exponential Growth | y = a(1+r)^t | Exponents |
| `topic_math_alg2_exp_decay` | Exponential Decay | y = a(1-r)^t | Growth |
| `topic_math_alg2_exp_e` | The Number e | Natural exponential base | Growth, Decay |
| `topic_math_alg2_exp_log` | Logarithms | Inverse of exponentials | Exponents |
| `topic_math_alg2_exp_log_props` | Properties of Logarithms | Product, quotient, power rules | Logarithms |

### 3. Geometry (topic_math_geom)

#### 3.1 Triangles (topic_math_geom_tri)

**Grade Level**: 9-10

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_math_geom_tri_classify` | Classifying Triangles | By sides and angles | Basic Geometry |
| `topic_math_geom_tri_angles` | Triangle Angle Sum | Interior angles = 180° | Classify |
| `topic_math_geom_tri_pythagorean` | Pythagorean Theorem | a² + b² = c² | Right Triangles |
| `topic_math_geom_tri_similar` | Similar Triangles | Proportional sides | Triangles |
| `topic_math_geom_tri_congruent` | Congruent Triangles | SSS, SAS, ASA, AAS | Similar |
| `topic_math_geom_tri_area` | Triangle Area | A = ½bh | Triangles |

#### 3.2 Circles (topic_math_geom_circle)

**Grade Level**: 10-11

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_math_geom_circle_parts` | Parts of a Circle | Radius, diameter, circumference | Basic Geometry |
| `topic_math_geom_circle_area` | Circle Area | A = πr² | Circle Parts |
| `topic_math_geom_circle_circumference` | Circumference | C = 2πr | Circle Parts |
| `topic_math_geom_circle_arcs` | Arcs and Sectors | Portions of circles | Circumference |
| `topic_math_geom_circle_tangent` | Tangent Lines | Lines touching at one point | Circle Parts |

### 4. Pre-Calculus (topic_math_precalc)

#### 4.1 Trigonometry (topic_math_precalc_trig)

**Grade Level**: 11-12

| Topic ID | Title | Description | Prerequisites |
|----------|-------|-------------|---------------|
| `topic_math_precalc_trig_ratios` | Trig Ratios | sin, cos, tan definitions | Right Triangles |
| `topic_math_precalc_trig_unit` | Unit Circle | Trig on the circle | Trig Ratios |
| `topic_math_precalc_trig_graphs` | Graphing Trig Functions | Sine and cosine waves | Unit Circle |
| `topic_math_precalc_trig_identities` | Trig Identities | Pythagorean, angle sum | Trig Functions |
| `topic_math_precalc_trig_inverse` | Inverse Trig Functions | arcsin, arccos, arctan | Trig Ratios |

#### 4.2 Limits (topic_math_precalc_limits) - Future

*(Preparation for Calculus - Post-MVP)*

---

## Topic Metadata

Each topic includes the following metadata:

```json
{
  "topic_id": "topic_phys_mech_newton_3",
  "title": "Newton's Third Law of Motion",
  "description": "For every action force, there is an equal and opposite reaction force",
  "subject": "physics",
  "unit": "Mechanics",
  "concept": "Newton's Laws",
  "grade_level_min": 9,
  "grade_level_max": 10,
  "difficulty_level": 3,
  "estimated_time_minutes": 3,
  "prerequisites": ["topic_phys_mech_newton_2"],
  "related_topics": [
    "topic_phys_mech_forces_net",
    "topic_phys_energy_momentum_def"
  ],
  "standards_alignment": {
    "ngss": ["HS-PS2-1"],
    "common_core_math": []
  },
  "keywords": [
    "action-reaction",
    "force pairs",
    "equal and opposite",
    "interaction forces"
  ],
  "typical_misconceptions": [
    "Action and reaction cancel out",
    "Reaction happens after action",
    "Only applies to collisions"
  ]
}
```

---

## Topic ID Naming Convention

### Format

```
topic_<subject>_<unit>_<concept>_<topic>
```

### Components

- **topic**: Always prefix with "topic\_"
- **subject**:
  - `phys` = Physics
  - `math` = Mathematics
  - `chem` = Chemistry (future)
  - `bio` = Biology (future)
- **unit**: Abbreviated unit name (e.g., `mech` = Mechanics)
- **concept**: Specific concept within unit
- **topic**: Specific topic (optional for leaf nodes)

### Examples

| Topic ID | Full Path |
|----------|-----------|
| `topic_phys` | Physics (root) |
| `topic_phys_mech` | Physics → Mechanics |
| `topic_phys_mech_newton` | Physics → Mechanics → Newton's Laws |
| `topic_phys_mech_newton_3` | Physics → Mechanics → Newton's Laws → Third Law |
| `topic_math_alg1_linear_slope` | Math → Algebra I → Linear Equations → Slope |

---

## Content Alignment

### Standards Mapping

#### Next Generation Science Standards (NGSS)

| NGSS Standard | Vividly Topics |
|---------------|----------------|
| HS-PS2-1 (Newton's 2nd Law) | topic_phys_mech_newton_2, topic_phys_mech_forces_net |
| HS-PS2-2 (Momentum) | topic_phys_energy_momentum_* |
| HS-PS3-1 (Energy) | topic_phys_energy_conservation |
| HS-PS3-2 (Energy Transfer) | topic_phys_energy_work_* |
| HS-PS4-1 (Waves) | topic_phys_waves_* |

#### Common Core Mathematics Standards

| CC Standard | Vividly Topics |
|-------------|----------------|
| HSA-REI.B.3 (Linear Equations) | topic_math_alg1_linear_solve |
| HSA-REI.C.6 (Systems) | topic_math_alg1_systems_* |
| HSF-IF.C.7 (Graphing) | topic_math_alg2_quad_graph |
| HSG-SRT.C.8 (Pythagorean) | topic_math_geom_tri_pythagorean |
| HSF-TF.A.1 (Trig Ratios) | topic_math_precalc_trig_ratios |

### Textbook Alignment

#### OpenStax Physics
- **Chapter 4**: Motion in Two Dimensions → topic_phys_mech_kinem_projectile
- **Chapter 5**: Newton's Laws → topic_phys_mech_newton_*
- **Chapter 7**: Work and Energy → topic_phys_energy_work_*
- **Chapter 14**: Waves → topic_phys_waves_*

#### OpenStax Algebra & Trigonometry
- **Chapter 2**: Linear Functions → topic_math_alg1_linear_*
- **Chapter 3**: Polynomial Functions → topic_math_alg1_poly_*
- **Chapter 5**: Exponential → topic_math_alg2_exp_*
- **Chapter 7**: Trigonometry → topic_math_precalc_trig_*

---

## Topic Statistics (MVP Target)

| Subject | Units | Concepts | Total Topics |
|---------|-------|----------|--------------|
| Physics | 3 | 12 | 65 |
| Mathematics | 4 | 14 | 75 |
| **Total** | **7** | **26** | **140** |

---

## Topic Expansion Roadmap

### Phase 2 (Post-MVP)
- Chemistry: Atomic Structure, Chemical Reactions, Stoichiometry
- Biology: Cell Biology, Genetics, Evolution
- Advanced Math: Calculus I basics

### Phase 3 (Year 2)
- AP-Level Content: AP Physics, AP Calculus
- Additional Sciences: Earth Science, Astronomy
- Statistics and Probability

---

**Document Control**
- **Owner**: Curriculum Team
- **Content Manager**: Vividly Curriculum Lead
- **Last Content Review**: October 2025
- **Next Review**: Monthly (during MVP)
