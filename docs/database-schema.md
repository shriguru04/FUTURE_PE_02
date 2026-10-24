# Database schema

All PKs are UUID. All tables have `created_at`; mutable ones have `updated_at`. Every owned table has `user_id` FK -> users.id ON DELETE CASCADE.

- **users**: email (unique, lowercased), password_hash, display_name, is_active
- **brands**: user_id, name, category, description, target_audience, voice, language, writing_style, messaging_guidelines, avoid_terms (JSON list), website_url, default_cta. UNIQUE(user_id, name)
- **products**: user_id, brand_id (CASCADE), name, description, features (JSON list), benefits (JSON list), price (numeric, null), intended_audience, supported_claims (JSON list), limitations, offer_details, cta
- **campaigns**: user_id, brand_id (RESTRICT), product_id (SET NULL), name, objective, platform (enum), status (enum: draft, in_progress, ready_for_review, approved, archived), settings (JSONB), notes. Indexes: (user_id, status), (user_id, platform), trigram/ILIKE on name
- **campaign_contents**: user_id, campaign_id (CASCADE), platform, section (enum: summary, hooks, primary_script, alt_scripts, caption, ctas, hashtags, variations, adaptation, claims_review), payload JSONB, current_version INT. UNIQUE(campaign_id, platform, section)
- **content_versions**: user_id, content_id (CASCADE), campaign_id, version_number, payload JSONB, source (enum: generation, section_regeneration, manual_edit, restore), generation_params JSONB. UNIQUE(content_id, version_number). Never updated or deleted except via campaign delete.
- **campaign_metrics**: user_id, campaign_id (CASCADE), metric_date, impressions, reach, video_views, clicks, conversions (all INT null, CHECK >= 0), spend, revenue (numeric null, CHECK >= 0), source (enum: manual, csv_import). Derived rates are computed at read time, never stored.
- **generation_jobs**: user_id, campaign_id, kind (full/section), status (running/succeeded/failed), provider, model, prompt_tokens, completion_tokens, error_code (no raw provider errors), duration_ms
- **audit_events**: user_id, action, entity_type, entity_id, ip (nullable), created_at

Deletion rules: deleting a brand with campaigns is blocked (409). Deleting a product keeps campaigns (product_id -> NULL). Deleting a campaign removes its contents, versions, metrics.

Note: string lists are stored as JSON (JSONB on PostgreSQL) so the same models run on SQLite in tests. Source of truth: `backend/app/models/entities.py` and `backend/alembic/versions/0001_initial.py`.
