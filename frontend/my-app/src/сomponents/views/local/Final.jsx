import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { css } from '../../../styles/styles.css';
import { motion, AnimatePresence } from 'framer-motion';

const Final = ({ isGitSubmitted, setIsGitSubmitted }) => {
    const navigate = useNavigate();
    const [showContent, setShowContent] = useState(false);
    const [showButtons, setShowButtons] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setShowContent(true);
        }, 500);

        const buttonsTimer = setTimeout(() => {
            setShowButtons(true);
        }, 1000);

        return () => {
            clearTimeout(timer);
            clearTimeout(buttonsTimer);
        };
    }, []);

    const handleNewProject = () => {
        setIsGitSubmitted(false);
        navigate('/main');
    };

    const handleArchitecture = () => {
        navigate('/stat/расход');
    };

    return (
        <css.FinalContainer>
            <AnimatePresence>
                {showContent && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.5 }}
                    >
                        <css.FinalTitle>
                            Анализ завершен!
                        </css.FinalTitle>
                        <css.FinalSubtitle>
                            Ваш проект успешно проанализирован
                        </css.FinalSubtitle>
                        <css.FinalText>
                            Теперь вы можете:
                        </css.FinalText>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {showButtons && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.5, delay: 0.3 }}
                        style={{ display: 'flex', gap: '20px', justifyContent: 'center' }}
                    >
                        <motion.div
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <css.FinalButton onClick={handleNewProject}>
                                Создать новый проект
                            </css.FinalButton>
                        </motion.div>
                        <motion.div
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <css.FinalButton onClick={handleArchitecture}>
                                Посмотреть архитектуру
                            </css.FinalButton>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1, delay: 1.5 }}
                style={{ marginTop: '40px' }}
            >
                <css.FinalSuccessIcon>
                    ✓
                </css.FinalSuccessIcon>
            </motion.div>
        </css.FinalContainer>
    );
};

export default Final; 