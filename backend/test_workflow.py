# test_workflow.py
try:
    from app.api import workflow
    print('✅ workflow import 성공')
    print('Router:', workflow.router)
    print('Routes:', [route.path for route in workflow.router.routes])
except Exception as e:
    print('❌ 오류:', e)
    import traceback
    traceback.print_exc()