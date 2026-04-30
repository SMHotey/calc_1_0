"""Fixed get_price_for_calculation that correctly handles shared IDs between tables."""

    def get_price_for_calculation(self, price_list_id: Optional[int], is_personalized: bool = False) -> Dict[str, float]:
        """
        Возвращает словарь цен для калькулятора, разрешая наследование из базового прайса.
        
        АВТОМАТИЧЕСКИ определяет тип прайс-листа по ID (проверяет обе таблицы).
        Параметр is_personalized используется только как подсказка.
        
        :param price_list_id: ID прайса (None = базовый)
        :param is_personalized: True если ID относится к персонализированному прайсу
        :return: Dict с ключами цен для PriceData
        """
        # Step 1: None -> базовый
        if price_list_id is None:
            base = self.get_base_price_list()
            logger.info(f"get_price_for_calculation: Using BASE (None)")
            return self._extract_prices(base)
        
        # Step 2: Get price list by ID - ВСЕГДА проверяем персонализированные ПЕРВЫМИ
        # Это необходимо, так как один и тот же ID может существовать в обеих таблицах
        # (например, первый персонализированный имеет ID=1, как и базовый)
        logger.info(f"get_price_for_calculation: Looking up ID={price_list_id}, is_personalized={is_personalized}")
        
        # ВСЕГДА сначала проверяем персонализированную таблицу
        price_list = self.personal_repo.get_by_id(price_list_id)
        if not price_list:
            # Не нашли в персонализированных - проверяем базовую
            price_list = self.base_repo.get_by_id(price_list_id)
        
        if price_list is None:
            # Не нашли ни в одной таблице, откатываемся к базовому
            logger.warning(f"get_price_for_calculation: FALLBACK to BASE (ID={price_list_id} not found)")
            return self._extract_prices(self.get_base_price_list())
        
        # Step 3: Обрабатываем в зависимости от типа
        from models.price_list import PersonalizedPriceList
        logger.info(f"get_price_for_calculation: Got price_list type={type(price_list).__name__}, id={getattr(price_list, 'id', None)}")
        
        if isinstance(price_list, PersonalizedPriceList):
            logger.info(f"get_price_for_calculation: Using PERSONALIZED (ID={price_list_id}, name={price_list.name})")
            
            # Обновляем объект из БД, чтобы получить последние значения custom_ полей
            self.session.expire(price_list)
            price_list = self.personal_repo.get_by_id(price_list_id)
            
            if not price_list:
                logger.warning(f"get_price_for_calculation: Personalized {price_list_id} not found after refresh")
                return self._extract_prices(self.get_base_price_list())
            
            # Получаем базовые цены из связанного базового прайса
            base_obj = self.base_repo.get_by_id(price_list.base_price_list_id)
            if not base_obj:
                base_obj = self.get_base_price_list()
            base_prices = self._extract_prices(base_obj)
            
            # Получаем персонализированные переопределения (custom_ поля)
            custom_fields = self._get_custom_fields(price_list)
            logger.info(f"get_price_for_calculation: custom_fields keys: {list(custom_fields.keys())}")
            logger.info(f"get_price_for_calculation: custom_doors_price_std_single = {custom_fields.get('doors_price_std_single')}")
            
            # Объединяем: базовые + персонализированные переопределения (только если значение не None)
            result = dict(base_prices)
            for k, v in custom_fields.items():
                if v is not None:
                    result[k] = v
                    logger.info(f"get_price_for_calculation: Overriding {k} = {v}")
            return result
        else:
            # Это базовый прайс-лист
            logger.info(f"get_price_for_calculation: Using BASE (ID={price_list_id})")
            return self._extract_prices(price_list)
