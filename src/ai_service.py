import os
import re
import time
import threading
from llama_cpp import Llama

class Llama_service:
    def __init__(self, model_path='C:/VSC/ai_models/Qwythos-9B-Claude/Qwythos-9B-Claude-Mythos-5-1M-MTP-Q5_K_M.gguf'):
         self.model_path = model_path
         self.llm = None

         self._load_thread = threading.Thread(target=self._load_model)
         self._load_thread.start() 
                
    def _load_model(self):
        if not os.path.exists(self.model_path):
            print('[AI_SERVICE] Модель не обнаружена!')
            return
        
        print('[AI_SERVICE]Началась фоновая загрузка модели...')
        self.llm = Llama(
            model_path=self.model_path,
            n_gpu_layers=-1,
            n_ctx=2048,
            verbose=False,
            flash_attention=True,
            )
    
    def wait_until_ready(self):
        if self._load_thread.is_alive():
            print('[AI_SERVICE] Ожидание завершения загрузки модели...')
            self._load_thread.join()
                
    def generate_answer(self, temp, rain, max_rain, place):
        self.wait_until_ready()
        system_role = (
            """You are a good football fan, your aim is to give an advice to another football fan how to dress on the coming football match.
            remember: people cant use umbrellas on football match. Youre getting some information about start match 
            (temperature on match time, rain probability, city) and max rain probability of the full day.
            give an advice to football fan and dont forget to say all the weather information. Response only in Russian language. 
            Dont use any text editing tools like markdown, html, etc. Dont use any emojis. Dont use any text formatting. Dont use any text decoration. 
            Dont use any text styling. Dont use any text coloring. Dont use any text underlining"""
            )

        prompt = (
            f'<|im_start|>system\n{system_role}<|im_end|>\n'
            f'<|im_start|>user\nwhole information about weather: temp on match start:{temp}, rain probability on match start:{rain}, max rain probability:{max_rain}, city:{place}<|im_end|>\n'
            f'<|im_start|>assistant\n'
        )

        start_time = time.perf_counter()

        response = self.llm(
            prompt=prompt,
            max_tokens=500,
            temperature=0.6,
            stop=['<|im_end|>']
        )

        
        raw_text = response['choices'][0]['text'].strip()
        clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()

        end_time = time.perf_counter() - start_time
        print(f'[AI_SERVICE] Ответ сгенерирован за: {end_time} с')

        tokens_generated = response['usage']['completion_tokens']
        tokens_per_second = tokens_generated / end_time if end_time > 0 else 0
        print(f'[AI_SERVICE] Сгенерировано токенов: {tokens_generated}, \nСкорость генерации: {tokens_per_second:.2f} токенов/сек')

        return clean_text
