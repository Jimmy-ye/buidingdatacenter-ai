"""
PC-UI 配置管理

提供灵活的 API 地址配置，支持环境变量
"""
import os


class Config:
    """配置类"""

    @staticmethod
    def get_api_base_url() -> str:
        """获取 API 基础地址"""
        # 从环境变量读取
        api_url = os.getenv('BDC_API_URL')
        if api_url:
            return api_url

        # 根据环境变量判断
        environment = os.getenv('ENVIRONMENT', 'development')

        if environment == 'production':
            # 生产环境：强制 HTTPS
            return 'https://api.example.com'
        elif environment == 'testing':
            return 'https://test-api.example.com'
        else:
            # 开发环境（默认）
            return 'http://127.0.0.1:8000/api/v1'

    @staticmethod
    def is_production() -> bool:
        """是否生产环境"""
        return os.getenv('ENVIRONMENT', 'development') == 'production'

    @staticmethod
    def is_development() -> bool:
        """是否开发环境"""
        return os.getenv('ENVIRONMENT', 'development') == 'development'

    @staticmethod
    def allow_default_login() -> bool:
        """是否允许默认登录（仅开发环境）"""
        return not Config.is_production()
