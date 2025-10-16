# pages/widgets/scheduling_algorithm.py
import random

class HeuristicScheduler:
    def __init__(self, orders, resources, setup_time=1):
        self.orders = sorted(orders, key=lambda o: o.get('priority', 0), reverse=True)
        self.resources = resources
        self.setup_time = setup_time
        self.schedule = {res: [] for res in resources}

    def run(self):
        for order in self.orders:
            best_fit = {'line': None, 'start_time': float('inf'), 'end_time': float('inf')}
            required_spec = self._get_spec_from_product(order['product'])
            
            for line_name, line_info in self.resources.items():
                if required_spec not in line_info['specs']:
                    continue
                
                last_task_end = 0; last_spec = None
                if self.schedule[line_name]:
                    last_task = self.schedule[line_name][-1]
                    last_task_end = last_task['end']
                    last_spec = self._get_spec_from_product(last_task['order']['product'])
                
                setup_needed = self.setup_time if last_spec and last_spec != required_spec else 0
                start_time = last_task_end + setup_needed
                
                if start_time < best_fit['start_time']:
                    best_fit = {'line': line_name, 'start_time': start_time, 'end_time': start_time + self._get_duration(order)}

            if best_fit['line']:
                self.schedule[best_fit['line']].append({'order': order, 'start': best_fit['start_time'], 'end': best_fit['end_time']})
        
        return self.schedule

    def _get_duration(self, order, speed=1000):
        return order['quantity'] / speed
        
    def _get_spec_from_product(self, product_name):
        if "5mm" in product_name: return "5mm"
        if "8mm" in product_name: return "8mm"
        return "unknown"