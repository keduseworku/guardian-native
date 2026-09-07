# Retained discrimination fixtures

These two deliberate-defect fixtures demonstrate that selected public-behavior probes
reject numerical overflow and stacked-wrapper ownership defects. Their targeted
corrections are applied to disposable copies inside test_discrimination.py. They are
regression controls, not a model-quality comparison.

The cache fixture is a previously generated candidate based on cachetools; its upstream
MIT license is retained in cache-seed/LICENSE. It is test data, not a runtime dependency.
The weighted fixture and local probe/correction code are covered by this repository's
MIT license. The package wheel excludes these fixtures; the source bundle includes them.
