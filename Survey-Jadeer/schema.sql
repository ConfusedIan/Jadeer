-- Jadeer Survey — database schema
-- Run this once in the Supabase SQL Editor (or via psql) to create the tables.

create table if not exists survey_responses (
    id uuid primary key default gen_random_uuid(),
    submitted_at timestamptz not null default now(),
    q1_skills_proof text not null,
    q2_cert_verification text not null,
    q3_cv_tailoring text not null,
    q4_cv_biggest_problem text not null,
    q5_rank_skills_assessment smallint not null,
    q5_rank_cert_verification smallint not null,
    q5_rank_cv_tailoring smallint not null,
    q5_rank_smart_matching smallint not null,
    constraint q5_rank_skills_assessment_range check (q5_rank_skills_assessment between 1 and 4),
    constraint q5_rank_cert_verification_range check (q5_rank_cert_verification between 1 and 4),
    constraint q5_rank_cv_tailoring_range check (q5_rank_cv_tailoring between 1 and 4),
    constraint q5_rank_smart_matching_range check (q5_rank_smart_matching between 1 and 4)
);

create index if not exists survey_responses_submitted_at_idx
    on survey_responses (submitted_at desc);
