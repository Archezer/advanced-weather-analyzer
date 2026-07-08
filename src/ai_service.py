import os
import re
import time
import asyncio
import threading
from llama_cpp import Llama

class Llama_service:
    def __init__(self, model_path='C:/VSC/ai_models/Qwythos-9B-Claude/Qwythos-9B-Claude-Mythos-5-1M-MTP-Q5_K_M.gguf'):
        self.model_path = model_path
        self.llm = None

        self._load_thread = threading.Thread(target=self._sync_load_model, daemon=True)
        self._load_thread.start()
                
    def _sync_load_model(self):
        if not os.path.exists(self.model_path):
            return
        
        self.llm = Llama(
            model_path=self.model_path,
            n_gpu_layers=-1,
            n_ctx=2048,
            verbose=False,
            flash_attention=True,
            )
                
    async def generate_answer(self, temp, rain, max_rain, activity, place):
        if self.llm is None:
            if self._load_thread.is_alive():
                print("[AI_SERVICE] Модель еще загружается в GPU... Ожидайте завершения.")
                await asyncio.to_thread(self._load_thread.join)
            self.load_model()

        system_role = (
            'You are a professional AI Stylist and Weather Consultant. Your goal is to advise the user on what to wear '
            'based on the weather forecast and their planned activity.\n'
            'STRICT RULES:\n'
            '1. Tailor your clothing suggestions precisely to the users activity. For example, if its a park walk, suggest comfortable shoes.'
            'If its a club night, suggest something stylish but consider the weather outside.\n'
            '2. Always analyze and explicitly mention ALL provided weather numbers (temperature, rain probabilities) so the user is informed.\n'
            '3. If umbrellas are mentioned, consider if they fit the activity (e.g., fine for a city walk, but highly inconvenient for a run or a stadium).\n'
            '4. Respond ONLY in Russian language. Keep the tone helpful, modern, and engaging.\n'
            '5. Use emojis for the weathers explanation\n'
            )

        prompt = (
            f'<|im_start|>system\n{system_role}<|im_end|>\n'
            f'<|im_start|>user\ncity:{place}.\n'
            f'Users planned activity: {activity}'
            f'whole information about weather: temp on match start:{temp}'
            f', rain probability on match start:{rain}, max rain probability:{max_rain}<|im_end|>'
            f'<|im_start|>assistant\n'
        )

        start_time = time.perf_counter()

        response = await asyncio.to_thread(
            self.llm,
            prompt=prompt,
            max_tokens=450,
            temperature=0.6,
            stop=['<|im_end|>']
        )

        
        raw_text = response['choices'][0]['text'].strip()
        clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()

        end_time = time.perf_counter() - start_time

        tokens_generated = response['usage']['completion_tokens']
        tokens_per_second = tokens_generated / end_time if end_time > 0 else 0
        print(f'[AI_SERVICE] Сгенерировано токенов: {tokens_generated}, \nСкорость генерации: {tokens_per_second:.2f} токенов/сек')

        return clean_text
