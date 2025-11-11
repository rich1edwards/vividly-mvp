-- =====================================================================
-- Migration: Add Expanded Interests with Icons for High School Students
-- =====================================================================
-- Description: Expands interests to 20 curated options for 9th-12th grade
-- students with icon support for better UX
-- Created: 2025-11-10
-- =====================================================================

-- Step 1: Add icon column to interests table
ALTER TABLE interests
ADD COLUMN IF NOT EXISTS icon VARCHAR(50);

COMMENT ON COLUMN interests.icon IS 'Icon identifier (lucide-react icon name or emoji)';

-- Step 2: Clear existing interests and insert comprehensive set
DELETE FROM interests;

-- Step 3: Insert 20 curated interests for American high school students
INSERT INTO interests (interest_id, name, category, description, icon, display_order) VALUES
    -- SPORTS & ATHLETICS (4 interests)
    ('basketball', 'Basketball', 'sports', 'Basketball and hoops', '🏀', 1),
    ('soccer', 'Soccer', 'sports', 'Soccer and futbol', '⚽', 2),
    ('football', 'Football', 'sports', 'American football', '🏈', 3),
    ('athletics', 'Track & Field', 'sports', 'Running, track, and athletics', '🏃', 4),

    -- ARTS & CREATIVITY (4 interests)
    ('music', 'Music', 'arts', 'Listening, playing, or producing music', '🎵', 10),
    ('art', 'Art & Drawing', 'arts', 'Drawing, painting, and visual arts', '🎨', 11),
    ('photography', 'Photography & Video', 'arts', 'Photography and videography', '📷', 12),
    ('dance', 'Dance', 'arts', 'Dance and performance', '💃', 13),

    -- TECHNOLOGY & DIGITAL (4 interests)
    ('video_games', 'Video Games', 'technology', 'Gaming and esports', '🎮', 20),
    ('coding', 'Coding & Tech', 'technology', 'Programming and technology', '💻', 21),
    ('social_media', 'Social Media', 'technology', 'Content creation and social platforms', '📱', 22),
    ('robotics', 'Robotics', 'technology', 'Robotics and engineering', '🤖', 23),

    -- SCIENCE & DISCOVERY (3 interests)
    ('space', 'Space & Astronomy', 'science', 'Space exploration and astronomy', '🚀', 30),
    ('biology', 'Biology & Nature', 'science', 'Living things and ecosystems', '🌿', 31),
    ('environmental', 'Environmental Science', 'science', 'Sustainability and climate', '🌎', 32),

    -- LIFESTYLE & CULTURE (5 interests)
    ('cooking', 'Cooking & Baking', 'lifestyle', 'Culinary arts and cooking', '🍳', 40),
    ('fashion', 'Fashion & Style', 'lifestyle', 'Fashion and personal style', '👗', 41),
    ('fitness', 'Fitness & Wellness', 'lifestyle', 'Exercise, sports, and health', '💪', 42),
    ('reading', 'Reading & Writing', 'lifestyle', 'Books, literature, and creative writing', '📚', 43),
    ('movies', 'Movies & TV', 'lifestyle', 'Films, shows, and entertainment', '🎬', 44)
ON CONFLICT (interest_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    icon = EXCLUDED.icon,
    display_order = EXCLUDED.display_order;

-- Verification query (comment out for production)
-- SELECT category, COUNT(*) as count FROM interests GROUP BY category ORDER BY category;
