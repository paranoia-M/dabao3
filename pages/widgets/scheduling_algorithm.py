# pages/widgets/scheduling_algorithm.py
import random

class HeuristicScheduler:
    def __init__(self, orders, resources, setup_time=1):
        """
        :param orders: list of order dicts, sorted by priority
        :param resources: dict of resource info, e.g., {'Line A': {'specs': ['5mm']}}
        :param setup_time: hours needed for changing specs
        """
        self.orders = sorted(orders, key=lambda o: o.get('priority', 0), reverse=True)
        self.resources = resources
        self.setup_time = setup_time
        self.schedule = {res: [] for res in resources} # {line: [{'order':..., 'start':..., 'end':...}]}

    def run(self):
        """执行启发式调度算法"""
        for order in self.orders:
            best_fit = {'line': None, 'start_time': float('inf'), 'end_time': float('inf')}
            
            required_spec = self._get_spec_from_product(order['product'])
            
            for line_name, line_info in self.resources.items():
                # 1. 检查资源约束
                if required_spec not in line_info['specs']:
                    continue
                
                # 2. 寻找最早可开始时间
                last_task_end = 0
                last_spec = None
                if self.schedule[line_name]:
                    last_task = self.schedule[line_name][-1]
                    last_task_end = last_task['end']
                    last_spec = self._get_spec_from_product(last_task['order']['product'])
                
                # 3. 计算换模时间
                setup_needed = self.setup_time if last_spec and last_spec != required_spec else 0
                start_time = last_task_end + setup_needed
                
                # 寻找更优解
                if start_time < best_fit['start_time']:
                    best_fit = {
                        'line': line_name,
                        'start_time': start_time,
                        'end_time': start_time + self._get_duration(order)
                    }

            # 分配到最佳位置
            if best_fit['line']:
                self.schedule[best_fit['line']].append({
                    'order': order,
                    'start': best_fit['start_time'],
                    'end': best_fit['end_time']
                })
        
        return self.schedule

    def _get_duration(self, order, speed=1000): # 假设1000米/小时
        return order['quantity'] / speed
        
    def _get_spec_from_product(self, product_name):
        # 简化版：从产品名中提取规格
        if "5mm" in product_name: return "5mm"
        if "8mm" in product_name: return "8mm"
        return "unknown"