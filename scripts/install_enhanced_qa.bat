@echo off
echo ====================================
echo Installing Enhanced Q&A Dependencies
echo ====================================

echo.
echo Installing core enhanced Q&A packages...
pip install sentence-transformers scikit-learn rank-bm25 torch

echo.
echo Installation complete!
echo.
echo Enhanced Q&A Agent is now ready with:
echo - Semantic search with sentence embeddings
echo - Advanced text similarity algorithms  
echo - Question classification
echo - Intelligent caching
echo - BM25 scoring
echo.
echo You can now use the enhanced Q&A features with:
echo   python main.py ask "your question here"
echo.
pause
