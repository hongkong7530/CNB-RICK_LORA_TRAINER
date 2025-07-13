import unittest
import json
from app import create_app
from app.database import get_db

class TaskStatusTestCase(unittest.TestCase):
    """测试任务状态接口"""
    
    def setUp(self):
        """测试前准备"""
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        """测试后清理"""
        self.app_context.pop()
    
    def test_get_task_status(self):
        """测试获取任务状态"""
        # 1. 创建一个测试任务
        task_data = {
            'name': '测试任务',
            'description': '这是一个测试任务'
        }
        response = self.client.post(
            '/api/v1/tasks',
            data=json.dumps(task_data),
            content_type='application/json'
        )
        # 验证HTTP状态码始终为200，因为我们将业务状态码放在code字段中
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result['code'], 0)  # 验证成功响应码
        task = result['data']
        task_id = task['id']
        
        # 2. 测试获取任务状态
        response = self.client.get(f'/api/v1/tasks/{task_id}/status')
        self.assertEqual(response.status_code, 200)
        
        # 验证返回的字段
        result = json.loads(response.data)
        self.assertEqual(result['code'], 0)  # 验证成功响应码
        status_data = result['data']
        self.assertEqual(status_data['id'], task_id)
        self.assertEqual(status_data['name'], '测试任务')
        self.assertEqual(status_data['status'], 'NEW')  # 新创建的任务状态应为NEW
        self.assertIn('progress', status_data)
        self.assertIn('recent_logs', status_data)
        
        # 3. 测试不存在的任务
        response = self.client.get('/api/v1/tasks/9999/status')
        # 业务错误也使用200作为HTTP状态码，但code字段表示业务错误
        result = json.loads(response.data)
        self.assertNotEqual(result['code'], 0)  # 验证错误响应码
        self.assertEqual(result['code'], 1001)  # 任务不存在错误码
        
if __name__ == '__main__':
    unittest.main() 