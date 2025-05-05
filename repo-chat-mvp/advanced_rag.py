import os
import openai
from jinja2 import Environment, FileSystemLoader
from vector_store import HybridStore

# Убедитесь, что переменная окружения OPENAI_API_KEY установлена
API_KEY = os.getenv("OPENAI_API_KEY")


class RAGCodeAssistant:
    def __init__(self, store: HybridStore, template_dir: str = None):
        """
        :param store: экземпляр HybridStore для гибридного поиска
        :param template_dir: папка с Jinja2-шаблоном system_prompt_template.jinja
        """
        self.store = store
        self.client = openai.OpenAI(
            api_key=API_KEY, api_base="https://api.vsegpt.ru/v1"
        )
        # Определяем директорию шаблонов
        if template_dir:
            self.template_dir = template_dir
        else:
            self.template_dir = os.path.join(os.path.dirname(__file__), "templates")

        # Настраиваем Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            keep_trailing_newline=True,
            lstrip_blocks=True,
            trim_blocks=True,
        )

    def answer(self, query: str) -> str:
        """
        Отвечает на запрос пользователя по коду в репозитории.
        """
        # 1) Получаем embedding запроса
        resp = self.client.embeddings.create(
            input=query, model="emb-openai/text-embedding-3-small"
        )
        qvec = resp.data[0].embedding
        q_tokens = query.split()

        # 2) Выполняем гибридный поиск по FAISS и BM25
        snips = self.store.query(qvec, q_tokens, top_k=5)

        # 3) Рендерим системный промпт по шаблону
        template = self.jinja_env.get_template("system_prompt_template.jinja")
        prompt = template.render(snips=snips, query=query)

        # 4) Отправляем запрос LLM
        chat = self.client.chat.completions.create(
            model="openai/gpt-4.1-nano",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.2,
        )
        return chat.choices[0].message.content
