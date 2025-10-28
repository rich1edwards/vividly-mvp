# Vividly Canonical Interests

**Version:** 1.0 (MVP)
**Last Updated:** October 27, 2025
**Total Interests:** 60

## Table of Contents

1. [Overview](#overview)
2. [Interest Categories](#interest-categories)
3. [Complete Interest List](#complete-interest-list)
4. [Interest Metadata](#interest-metadata)
5. [Fallback Strategy](#fallback-strategy)
6. [Expansion Guidelines](#expansion-guidelines)

---

## Overview

Canonical interests represent the complete, curated list of topics used to personalize learning content. Students rank their top interests, which are then used to generate contextual analogies and examples in STEM lessons.

### Design Principles

1. **Relatable**: Interests must be familiar to high school students
2. **Diverse**: Span different categories (sports, arts, technology, etc.)
3. **Generative**: Rich enough to inspire creative analogies
4. **Safe**: Pre-vetted to avoid inappropriate content
5. **Age-Appropriate**: Suitable for 14-18 year-olds

### Why Canonical?

- **Safety**: Prevents students from entering inappropriate interests
- **Quality**: Ensures our AI can generate high-quality analogies
- **Consistency**: Improves caching efficiency
- **Moderation**: Easier content review and filtering

---

## Interest Categories

| Category | Count | Examples |
|----------|-------|----------|
| **Sports** | 12 | Basketball, Soccer, Swimming |
| **Arts & Music** | 10 | Music Production, Drawing, Photography |
| **Technology** | 9 | Video Games, Coding, Robotics |
| **Entertainment** | 8 | Movies, Streaming, Social Media |
| **Outdoor & Nature** | 6 | Hiking, Camping, Gardening |
| **Hobbies & Crafts** | 7 | Cooking, Fashion, DIY |
| **Culture & Social** | 5 | Reading, History, Languages |
| **Other** | 3 | Animals, Cars, Space |

**Total**: 60 interests

---

## Complete Interest List

### Sports (12)

| Interest ID | Name | Description | Example Analogy |
|-------------|------|-------------|-----------------|
| `int_basketball` | Basketball | Playing and watching basketball | Newton's 3rd Law: When you jump for a rebound, you push down on the floor (action) and the floor pushes you up (reaction) |
| `int_soccer` | Soccer / Football | Playing and watching soccer | Projectile motion: Kicking a soccer ball follows a parabolic path |
| `int_football` | American Football | Playing and watching football | Momentum: A linebacker tackling a quarterback demonstrates conservation of momentum |
| `int_baseball` | Baseball | Playing and watching baseball | Circular motion: A pitcher's arm undergoes circular motion when throwing |
| `int_track_field` | Track & Field | Running, jumping, throwing | Kinematics: Sprinters accelerate from blocks following physics equations |
| `int_swimming` | Swimming | Competitive or recreational swimming | Fluid dynamics: Swimmers minimize drag to move faster |
| `int_tennis` | Tennis | Playing and watching tennis | Work and energy: Racket transfers energy to ball |
| `int_volleyball` | Volleyball | Playing and watching volleyball | Projectile motion: Setting a volleyball follows parabolic trajectory |
| `int_skateboarding` | Skateboarding | Skateboard tricks and culture | Angular momentum: Spinning during tricks conserves angular momentum |
| `int_dance` | Dance | Hip-hop, ballet, contemporary | Rotational motion: Pirouettes demonstrate angular velocity |
| `int_martial_arts` | Martial Arts | Karate, taekwondo, MMA | Newton's laws: Breaking boards shows force and acceleration |
| `int_fitness` | Fitness & Gym | Working out, strength training | Biomechanics: Lifting weights demonstrates force and torque |

### Arts & Music (10)

| Interest ID | Name | Description | Example Analogy |
|-------------|------|-------------|-----------------|
| `int_music_production` | Music Production | Creating beats and songs | Waves: Sound waves have frequency and amplitude like music notes |
| `int_playing_instrument` | Playing Music | Guitar, piano, drums, etc. | Harmonic motion: Guitar strings vibrate at specific frequencies |
| `int_singing` | Singing | Vocal performance | Resonance: Vocal cords resonate to produce different pitches |
| `int_drawing` | Drawing & Sketching | Pencil, digital art | Geometry: Perspective drawing uses angles and proportions |
| `int_painting` | Painting | Watercolor, acrylic, oil | Optics: Mixing colors follows additive/subtractive color theory |
| `int_photography` | Photography | Taking photos, editing | Optics: Camera lenses focus light using refraction |
| `int_videography` | Videography | Filming and editing videos | Frame rate: 24 fps relates to persistence of vision |
| `int_graphic_design` | Graphic Design | Digital design, logos | Vectors: Design software uses mathematical vectors |
| `int_theater` | Theater & Drama | Acting, stagecraft | Acoustics: Theater design optimizes sound reflection |
| `int_animation` | Animation | 2D/3D animation | Linear interpolation: Animation uses math to transition frames |

### Technology (9)

| Interest ID | Name | Description | Example Analogy |
|-------------|------|-------------|-----------------|
| `int_video_games` | Video Games | Playing and designing games | Vectors: Game engines use vectors for character movement |
| `int_coding` | Coding & Programming | Writing software | Algorithms: Sorting algorithms demonstrate efficiency (Big O) |
| `int_robotics` | Robotics | Building and programming robots | Kinematics: Robot arms use forward/inverse kinematics |
| `int_computers` | Computers & Tech | Building PCs, hardware | Electricity: Circuits power computer components |
| `int_phones` | Smartphones & Apps | Mobile technology | Binary: Phones store data in bits and bytes |
| `int_social_media` | Social Media | Instagram, TikTok, Twitter | Networks: Social graphs use graph theory |
| `int_ai_ml` | Artificial Intelligence | AI, machine learning | Linear algebra: Neural networks use matrix operations |
| `int_web_design` | Web Design | Creating websites | Coordinates: CSS positioning uses coordinate systems |
| `int_cybersecurity` | Cybersecurity | Hacking, security | Cryptography: Encryption uses number theory |

### Entertainment (8)

| Interest ID | Name | Description | Example Analogy |
|-------------|------|-------------|-----------------|
| `int_movies` | Movies & Film | Watching and analyzing films | Optics: Projectors use lenses to display images |
| `int_tv_shows` | TV Shows & Streaming | Binge-watching shows | Data compression: Streaming uses algorithms to reduce file size |
| `int_youtube` | YouTube & Content Creation | Creating/watching videos | Bandwidth: Video quality depends on data transfer rate |
| `int_anime_manga` | Anime & Manga | Japanese animation and comics | Motion blur: Animation frame rate affects perception |
| `int_comic_books` | Comic Books & Superheroes | Marvel, DC, manga | Physics: Superhero powers often violate (or use!) physics |
| `int_podcasts` | Podcasts | Listening to podcasts | Sound waves: Podcast audio is digitized sound waves |
| `int_reading` | Reading & Books | Fiction, non-fiction | Information theory: Books encode information in text |
| `int_writing` | Creative Writing | Stories, poetry, blogs | Statistics: Word frequency follows Zipf's law |

### Outdoor & Nature (6)

| Interest ID | Name | Description | Example Analogy |
|-------------|------|-------------|-----------------|
| `int_hiking` | Hiking & Camping | Outdoor adventures | Potential energy: Hiking uphill increases gravitational PE |
| `int_fishing` | Fishing | Freshwater and saltwater fishing | Tension: Fishing line experiences tension force |
| `int_gardening` | Gardening & Plants | Growing plants | Photosynthesis: Plants convert light energy to chemical energy |
| `int_environment` | Environmental Science | Conservation, climate | Thermodynamics: Heat transfer affects climate systems |
| `int_weather` | Weather & Meteorology | Storms, forecasting | Fluid dynamics: Air masses interact to create weather |
| `int_astronomy` | Astronomy & Space | Stars, planets, cosmos | Gravity: Planetary orbits follow gravitational laws |

### Hobbies & Crafts (7)

| Interest ID | Name | Description | Example Analogy |
|-------------|------|-------------|-----------------|
| `int_cooking` | Cooking & Baking | Food preparation | Thermodynamics: Cooking involves heat transfer |
| `int_fashion` | Fashion & Style | Clothing, trends | Geometry: Pattern-making uses geometric shapes |
| `int_makeup` | Makeup & Beauty | Cosmetics application | Optics: Makeup artists use color theory and light |
| `int_diy_crafts` | DIY & Crafts | Making things by hand | Engineering: Crafts use mechanical principles |
| `int_woodworking` | Woodworking | Building with wood | Torque: Using wrenches and screws demonstrates torque |
| `int_sewing` | Sewing & Textiles | Making clothes | Tension: Thread tension is critical for sewing |
| `int_jewelry` | Jewelry Making | Designing accessories | Crystallography: Gemstones have crystal structures |

### Culture & Social (5)

| Interest ID | Name | Description | Example Analogy |
|-------------|------|-------------|-----------------|
| `int_history` | History | World events, civilizations | Timelines: Historical events use chronological ordering |
| `int_languages` | Learning Languages | Foreign languages | Information theory: Languages encode meaning |
| `int_travel` | Travel & Geography | Exploring places | Coordinate systems: GPS uses latitude/longitude |
| `int_volunteering` | Volunteering & Community | Helping others | Networks: Community organization uses graph structures |
| `int_debate` | Debate & Public Speaking | Argumentation | Logic: Debate uses logical reasoning |

### Other (3)

| Interest ID | Name | Description | Example Analogy |
|-------------|------|-------------|-----------------|
| `int_animals` | Animals & Pets | Caring for animals | Biomechanics: Animal movement uses physics |
| `int_cars` | Cars & Vehicles | Automobiles, racing | Mechanics: Car engines demonstrate thermodynamic cycles |
| `int_business` | Business & Entrepreneurship | Starting businesses | Economics: Supply and demand use functions |

---

## Interest Metadata

Each interest includes rich metadata for content generation:

```json
{
  "interest_id": "int_basketball",
  "name": "Basketball",
  "description": "Playing and watching basketball - shooting hoops, dribbling, teamwork",
  "category": "sports",

  "common_terms": [
    "shooting", "dribbling", "passing", "rebounding",
    "layup", "free throw", "three-pointer", "dunk",
    "court", "hoop", "backboard", "net"
  ],

  "example_scenarios": [
    "When you jump for a shot, you push down on the floor",
    "A basketball flying through the air follows a parabolic arc",
    "The ball bounces because of elastic potential energy"
  ],

  "subject_affinity": {
    "physics": 0.95,
    "mathematics": 0.75,
    "chemistry": 0.20,
    "biology": 0.40
  },

  "difficulty_generating": {
    "easy": ["mechanics", "projectile_motion", "energy"],
    "medium": ["rotation", "momentum", "waves"],
    "hard": ["electromagnetism", "quantum"]
  },

  "icon_url": "/assets/icons/basketball.svg",
  "hero_image_url": "/assets/heroes/basketball.jpg",

  "is_active": true,
  "display_order": 1,
  "popularity_score": 95
}
```

---

## Fallback Strategy

When a student's top-ranked interest cannot generate good content for a topic, the system uses this fallback hierarchy:

### Fallback Order

1. **Primary Interest**: Student's #1 ranked interest
2. **Secondary Interest**: Student's #2 ranked interest
3. **Tertiary Interest**: Student's #3 ranked interest
4. **Subject-Aligned Default**: Use most popular interest for that subject
5. **Universal Fallback**: Use "sports" or "music" (high generalizability)
6. **Neutral Mode**: Generate content without personalization

### Subject-Aligned Defaults

| Subject | Default Interests (in order) |
|---------|------------------------------|
| Physics | Sports → Technology → Music |
| Mathematics | Coding → Video Games → Business |
| Chemistry | Cooking → Environment → DIY |
| Biology | Animals → Gardening → Fitness |

### Implementation

```python
def get_interest_for_topic(student_interests: list, topic_id: str) -> str:
    """
    Select best interest for generating content for a topic.
    """
    subject = get_topic_subject(topic_id)

    # Try student's ranked interests
    for interest in student_interests[:3]:
        if can_generate_quality_content(interest, topic_id):
            return interest

    # Fallback to subject-aligned defaults
    defaults = SUBJECT_DEFAULTS[subject]
    for default_interest in defaults:
        if can_generate_quality_content(default_interest, topic_id):
            return default_interest

    # Universal fallback
    return "int_sports_general"
```

### Quality Check

```python
def can_generate_quality_content(interest_id: str, topic_id: str) -> bool:
    """
    Determine if interest can generate quality analogies for topic.
    """
    interest = get_interest(interest_id)
    topic = get_topic(topic_id)

    # Check subject affinity score
    affinity = interest["subject_affinity"].get(topic["subject"], 0)
    if affinity < 0.3:
        return False

    # Check difficulty compatibility
    topic_difficulty = topic["difficulty_level"]
    if topic_difficulty not in interest["difficulty_generating"]["easy"] + \
                                 interest["difficulty_generating"]["medium"]:
        return False

    return True
```

---

## Interest Selection UI

### Student Interface

Students select and rank up to **5 interests** during onboarding:

```
╔════════════════════════════════════════════╗
║   What are you interested in?              ║
║   (Select up to 5, then drag to rank)      ║
╠════════════════════════════════════════════╣
║                                            ║
║   🏀 Basketball               [Selected]   ║
║   🎮 Video Games              [Selected]   ║
║   🎵 Music Production         [Selected]   ║
║   ⚽ Soccer                    [Select]     ║
║   🎬 Movies                    [Select]     ║
║   💻 Coding                    [Select]     ║
║   ...                                      ║
║                                            ║
║   ┌────────────────────────────┐           ║
║   │ Your Top Interests:        │           ║
║   │ 1. 🏀 Basketball           │           ║
║   │ 2. 🎮 Video Games          │           ║
║   │ 3. 🎵 Music Production     │           ║
║   └────────────────────────────┘           ║
║                                            ║
║              [Continue]                    ║
╚════════════════════════════════════════════╝
```

### Teacher Override

Teachers can suggest interests for specific lessons:

```
Assign Content to Class
━━━━━━━━━━━━━━━━━━━━━━━━━━
Topic: Newton's Third Law
Default: Use student interests

Override for this assignment:
┌─────────────────────────────┐
│ Suggest Interest (optional) │
│ [Basketball ▼]              │
└─────────────────────────────┘

Reason: We just discussed basketball
        in class as an example
```

---

## Expansion Guidelines

### Adding New Interests

**Criteria for new interests:**

1. **Popularity**: Must resonate with >5% of target demographic
2. **Generalizability**: Can create analogies for >50% of topics
3. **Age-Appropriate**: Suitable for 14-18 year-olds
4. **Culturally Sensitive**: Inclusive and respectful
5. **Content Safety**: Won't generate inappropriate content

**Process:**

1. Research: Survey students for popular interests
2. Proposal: Submit interest proposal with metadata
3. Testing: Generate 10 sample analogies across different topics
4. Review: Content team reviews for quality and safety
5. Approval: Curriculum manager approves for production
6. Deployment: Add to database and re-train models

### Seasonal/Trending Interests

**Future consideration**: Allow temporary trending interests

- Olympics → `int_olympics` (active during Olympic games)
- World Cup → `int_world_cup` (active during tournament)
- New movie/game → `int_star_wars_2025` (limited time)

**Rules:**
- Maximum 10 trending interests active at once
- Auto-deactivate after event/trend passes
- Clearly marked as "trending" in UI

---

## Interest Analytics

### Track Interest Performance

```sql
-- Most popular interests
SELECT
    i.name,
    COUNT(DISTINCT si.student_id) AS student_count,
    AVG(si.rank) AS avg_rank
FROM student_interests si
JOIN interests i ON si.interest_id = i.id
GROUP BY i.id, i.name
ORDER BY student_count DESC
LIMIT 20;

-- Interest effectiveness (by rating)
SELECT
    i.name AS interest,
    t.subject,
    COUNT(*) AS content_count,
    AVG(f.rating) AS avg_rating
FROM generated_content gc
JOIN interests i ON gc.interest_id = i.id
JOIN topics t ON gc.topic_id = t.id
LEFT JOIN feedback f ON gc.id = f.content_id
WHERE f.rating IS NOT NULL
GROUP BY i.name, t.subject
HAVING COUNT(*) >= 10
ORDER BY avg_rating DESC;
```

### Interest Coverage Heatmap

| Interest / Subject | Physics | Math | Chemistry | Biology |
|--------------------|---------|------|-----------|---------|
| Basketball | ✅ 95% | ✅ 75% | ⚠️ 40% | ✅ 60% |
| Video Games | ✅ 85% | ✅ 90% | ⚠️ 35% | ⚠️ 45% |
| Music Production | ✅ 90% | ✅ 70% | ⚠️ 30% | ⚠️ 35% |
| Cooking | ✅ 70% | ⚠️ 50% | ✅ 95% | ✅ 80% |
| Animals | ✅ 65% | ⚠️ 45% | ✅ 75% | ✅ 98% |

Legend:
- ✅ >70%: Excellent coverage
- ⚠️ 40-70%: Moderate coverage
- ❌ <40%: Poor coverage (use fallback)

---

**Document Control**
- **Owner**: Content Team & Curriculum Manager
- **Last Interest Added**: October 2025
- **Next Review**: Monthly (during MVP)
- **Student Feedback**: Collected via in-app surveys
