-- Jadeer Survey database schema
-- Run this once in the Supabase SQL Editor (or via psql) to create the table.

drop table if exists survey_responses;

create table survey_responses (
    id uuid primary key default gen_random_uuid(),
    submitted_at timestamptz not null default now(),
    q0_status text not null,
    q1_assessment_feedback text not null,
    q2_certification_value text not null,
    q3_cv_tailoring_feedback text not null,
    q4_friend_advice text not null,
    q5_rank_assessment smallint not null,
    q5_rank_cert_verification smallint not null,
    q5_rank_cv_recommendations smallint not null,
    q5_rank_cv_generation smallint not null,
    q5_rank_company_search smallint not null,
    q6_open_feedback text,
    constraint q5_assessment_range check (q5_rank_assessment between 1 and 5),
    constraint q5_cert_range check (q5_rank_cert_verification between 1 and 5),
    constraint q5_cv_recs_range check (q5_rank_cv_recommendations between 1 and 5),
    constraint q5_cv_gen_range check (q5_rank_cv_generation between 1 and 5),
    constraint q5_company_search_range check (q5_rank_company_search between 1 and 5)
);

create index if not exists survey_responses_submitted_at_idx
    on survey_responses (submitted_at desc);
