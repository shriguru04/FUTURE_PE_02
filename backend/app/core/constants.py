PLATFORMS = ("instagram_reels", "facebook_video", "youtube_shorts", "tiktok", "website_video")
STATUSES = ("draft", "in_progress", "ready_for_review", "approved", "archived")
SECTIONS = (
    "summary", "hooks", "primary_script", "alt_scripts", "caption",
    "ctas", "hashtags", "variations", "adaptation", "claims_review",
)
CONTENT_FORMATS = (
    "problem_solution", "product_demo", "educational", "founder_story",
    "unboxing", "faq", "lifestyle", "offer_based",
)
VERSION_SOURCES = ("generation", "section_regeneration", "manual_edit", "restore", "duplicate")
EXPORT_FORMATS = ("txt", "md", "json", "pdf")
METRIC_SOURCES = ("manual", "csv_import")  # only "manual" is implemented in the API
