-- Run this SQL in the Supabase Dashboard SQL Editor:
-- https://supabase.com/dashboard/project/qgjrfyvndhusydplqgnp/sql/new

CREATE TABLE IF NOT EXISTS public.assessment_results (
  id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id           UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  occupation_title  TEXT NOT NULL,
  occupation_code   TEXT NOT NULL,
  skill_name        TEXT NOT NULL,
  skill_category    TEXT,
  skill_priority    TEXT,
  score             INTEGER NOT NULL,
  total_questions   INTEGER NOT NULL,
  percentage        INTEGER NOT NULL,
  passed            BOOLEAN NOT NULL,
  pass_threshold    INTEGER,
  threshold_reason  TEXT,
  question_results  JSONB,
  assessed_at       TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.assessment_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert their own results"
  ON public.assessment_results FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own results"
  ON public.assessment_results FOR SELECT
  USING (auth.uid() = user_id);
