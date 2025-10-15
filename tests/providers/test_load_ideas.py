import sys
sys.path.insert(0, '../providers/jules')
from orchestrator import JulesOrchestrator, RepoConfig

config = RepoConfig(
    owner='test-owner',
    token='test-token',
    max_concurrent=1
)

orchestrator = JulesOrchestrator(config, 'test-augment-token')

try:
    ideas = orchestrator.load_ideas('../data/ideas.csv')
    print(f"✅ Loaded {len(ideas)} ideas")
    for idea in ideas:
        print(f"   - {idea.title}: has_experiments={idea.has_experiments}")
except Exception as e:
    print(f"❌ Load failed: {e}")
    import traceback
    traceback.print_exc()
