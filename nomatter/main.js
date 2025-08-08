import React, { useState, useCallback } from 'react';
import { Download, Upload, Search, RefreshCw, FileText, CheckCircle } from 'lucide-react';

const ExcelTextReplacer = () => {
  const [file, setFile] = useState(null);
  const [workbook, setWorkbook] = useState(null);
  const [foundThemes, setFoundThemes] = useState([]);
  const [selectedTheme, setSelectedTheme] = useState('');
  const [customTheme, setCustomTheme] = useState('');
  const [replacements, setReplacements] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('');

  const handleFileUpload = useCallback(async (event) => {
    const uploadedFile = event.target.files[0];
    if (!uploadedFile) return;

    setFile(uploadedFile);
    setStatus('Загрузка файла...');

    try {
      // Читаем файл
      const arrayBuffer = await uploadedFile.arrayBuffer();
      const uint8Array = new Uint8Array(arrayBuffer);
      
      // Используем SheetJS для чтения Excel файла
      const XLSX = await import('https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js');
      const wb = XLSX.read(uint8Array, { type: 'array', cellStyles: true });
      
      setWorkbook(wb);
      
      // Анализируем темы в файле
      const sheet = wb.Sheets["Таргет 2025"] || wb.Sheets[wb.SheetNames[0]];
      const themes = new Set();
      
      // Ищем все ячейки с "Тема:"
      for (let row = 2; row <= 300; row++) {
        for (let colCode = 65; colCode <= 90; colCode++) {
          const col = String.fromCharCode(colCode);
          const cellAddr = col + row;
          const cell = sheet[cellAddr];
          
          if (cell && cell.v && typeof cell.v === 'string' && cell.v.includes('Тема:')) {
            const lines = cell.v.split('\n');
            const themeLineIndex = lines.findIndex(line => line.includes('Тема:'));
            if (themeLineIndex >= 0) {
              const themeLine = lines[themeLineIndex].trim();
              themes.add(themeLine);
            }
          }
        }
      }
      
      setFoundThemes(Array.from(themes));
      setStatus(`Файл загружен успешно. Найдено ${themes.size} уникальных тем.`);
      
    } catch (error) {
      setStatus(`Ошибка при загрузке файла: ${error.message}`);
      console.error(error);
    }
  }, []);

  const analyzeReplacements = useCallback(() => {
    if (!workbook) return;
    
    const themeToReplace = selectedTheme || customTheme;
    if (!themeToReplace) {
      setStatus('Выберите или введите тему для замены');
      return;
    }

    setIsProcessing(true);
    setStatus('Анализ файла...');

    try {
      const sheet = workbook.Sheets["Таргет 2025"] || workbook.Sheets[workbook.SheetNames[0]];
      const foundReplacements = [];

      // Ищем все ячейки с выбранной темой
      for (let row = 2; row <= 300; row++) {
        const rowName = sheet[`B${row}`]?.v;
        if (!rowName) continue;

        for (let colCode = 65; colCode <= 90; colCode++) {
          const col = String.fromCharCode(colCode);
          const cellAddr = col + row;
          const cell = sheet[cellAddr];

          if (cell && cell.v && typeof cell.v === 'string' && 
              cell.v.includes(themeToReplace)) {
            
            const lines = cell.v.split('\n');
            const firstLine = lines[0].trim();
            
            // Извлекаем URL (убираем "- таргет на ...")
            const url = firstLine.split(' - таргет на')[0].trim();
            
            // Создаем название района (убираем "Про " и делаем заглавными)
            const districtName = rowName.replace('Про ', '').toUpperCase();
            
            // Формируем новый текст
            const newText = `${url}  ЦР25_${districtName}_ОТКРЫТЫЙВАО`;

            foundReplacements.push({
              address: cellAddr,
              row: row,
              col: col,
              rowName: rowName,
              districtName: districtName,
              url: url,
              oldText: cell.v,
              newText: newText
            });
          }
        }
      }

      setReplacements(foundReplacements);
      setStatus(`Найдено ${foundReplacements.length} ячеек для замены`);

    } catch (error) {
      setStatus(`Ошибка при анализе: ${error.message}`);
      console.error(error);
    } finally {
      setIsProcessing(false);
    }
  }, [workbook, selectedTheme, customTheme]);

  const applyReplacements = useCallback(() => {
    if (!workbook || replacements.length === 0) return;

    setIsProcessing(true);
    setStatus('Применение изменений...');

    try {
      const sheet = workbook.Sheets["Таргет 2025"] || workbook.Sheets[workbook.SheetNames[0]];

      // Применяем все замены
      replacements.forEach(replacement => {
        const cell = sheet[replacement.address];
        if (cell) {
          cell.v = replacement.newText;
          cell.w = replacement.newText;
          cell.t = 's'; // Тип ячейки - строка
        }
      });

      setStatus(`Изменения применены к ${replacements.length} ячейкам`);

    } catch (error) {
      setStatus(`Ошибка при применении изменений: ${error.message}`);
      console.error(error);
    } finally {
      setIsProcessing(false);
    }
  }, [workbook, replacements]);

  const downloadFile = useCallback(async () => {
    if (!workbook) return;

    try {
      const XLSX = await import('https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js');
      
      // Генерируем новый файл Excel
      const wbout = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      
      // Создаем Blob и скачиваем файл
      const blob = new Blob([wbout], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `Обновленный_${file?.name || 'файл.xlsx'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setStatus('Файл скачан успешно');
      
    } catch (error) {
      setStatus(`Ошибка при скачивании: ${error.message}`);
      console.error(error);
    }
  }, [workbook, file]);

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Автоматизированный отчет - Замена текста в Excel
        </h1>
        <p className="text-gray-600">
          Замена текста "Тема: Проект «Открывай ВАО»..." на формат "ЦР25_РАЙОН_ОТКРЫТЫЙВАО"
        </p>
      </div>

      {/* Загрузка файла */}
      <div className="mb-6 p-4 border-2 border-dashed border-gray-300 rounded-lg">
        <div className="flex items-center justify-center">
          <Upload className="mr-2" size={20} />
          <label className="cursor-pointer text-blue-600 hover:text-blue-800">
            Выбрать Excel файл
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
        {file && (
          <p className="text-center text-sm text-gray-600 mt-2">
            Загружен: {file.name}
          </p>
        )}
      </div>

      {/* Выбор темы для замены */}
      {foundThemes.length > 0 && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-3">Шаг 1: Выберите тему для замены</h3>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Выберите из найденных тем:
            </label>
            <select
              value={selectedTheme}
              onChange={(e) => {
                setSelectedTheme(e.target.value);
                setCustomTheme('');
              }}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              <option value="">-- Выберите тему --</option>
              {foundThemes.map((theme, index) => (
                <option key={index} value={theme}>
                  {theme}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Или введите тему вручную:
            </label>
            <input
              type="text"
              value={customTheme}
              onChange={(e) => {
                setCustomTheme(e.target.value);
                setSelectedTheme('');
              }}
              placeholder="Например: Тема: Проект «Открывай ВАО»..."
              className="w-full p-2 border border-gray-300 rounded-md"
            />
          </div>

          <button
            onClick={analyzeReplacements}
            disabled={(!selectedTheme && !customTheme) || isProcessing}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            <Search className="mr-2" size={16} />
            {isProcessing ? 'Поиск...' : 'Найти ячейки для замены'}
          </button>
        </div>
      )}

      {/* Результаты поиска */}
      {replacements.length > 0 && (
        <div className="mb-6 p-4 bg-green-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-3">
            Шаг 2: Найдено {replacements.length} ячеек для замены
          </h3>
          
          <div className="max-h-64 overflow-y-auto mb-4">
            {replacements.slice(0, 5).map((replacement, index) => (
              <div key={index} className="mb-3 p-3 bg-white border rounded-md text-sm">
                <div className="font-medium text-gray-800">
                  {replacement.address}: {replacement.rowName}
                </div>
                <div className="text-gray-600 mt-1">
                  <strong>Было:</strong> {replacement.oldText.substring(0, 100)}...
                </div>
                <div className="text-green-700 mt-1">
                  <strong>Будет:</strong> {replacement.newText}
                </div>
              </div>
            ))}
            {replacements.length > 5 && (
              <div className="text-center text-gray-500 text-sm">
                ... и еще {replacements.length - 5} ячеек
              </div>
            )}
          </div>

          <button
            onClick={applyReplacements}
            disabled={isProcessing}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 mr-3"
          >
            <CheckCircle className="mr-2" size={16} />
            {isProcessing ? 'Применение...' : 'Применить изменения'}
          </button>
        </div>
      )}

      {/* Скачивание файла */}
      {workbook && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-3">Шаг 3: Скачать обновленный файл</h3>
          <button
            onClick={downloadFile}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Download className="mr-2" size={16} />
            Скачать обновленный Excel файл
          </button>
        </div>
      )}

      {/* Статус */}
      {status && (
        <div className="mt-4 p-3 bg-gray-100 rounded-md">
          <div className="flex items-center">
            <FileText className="mr-2" size={16} />
            <span className="text-sm text-gray-700">{status}</span>
          </div>
        </div>
      )}

      {/* Инструкция */}
      <div className="mt-8 p-4 bg-yellow-50 rounded-lg">
        <h4 className="font-semibold text-yellow-800 mb-2">Инструкция по использованию:</h4>
        <ol className="text-sm text-yellow-700 space-y-1">
          <li>1. Загрузите Excel файл с таргетингом</li>
          <li>2. Выберите тему, которую нужно заменить, из списка или введите вручную</li>
          <li>3. Нажмите "Найти ячейки для замены" для анализа</li>
          <li>4. Просмотрите найденные ячейки и нажмите "Применить изменения"</li>
          <li>5. Скачайте обновленный файл</li>
        </ol>
        <p className="text-sm text-yellow-700 mt-2">
          <strong>Формат замены:</strong> URL + " ЦР25_НАЗВАНИЕ_РАЙОНА_ОТКРЫТЫЙВАО"
        </p>
      </div>
    </div>
  );
};

export default ExcelTextReplacer;