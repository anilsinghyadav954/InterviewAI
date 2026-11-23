import { jsPDF } from 'jspdf';

/**
 * Generates and downloads a clean, multi-page professional PDF report
 * from interview evaluation data.
 */
export const exportInterviewReportPDF = (report, candidateName = 'Candidate') => {
  if (!report) return;

  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 16;
  const contentWidth = pageWidth - margin * 2;
  let y = 18;

  const checkPageBreak = (neededHeight) => {
    if (y + neededHeight > pageHeight - 16) {
      doc.addPage();
      y = 18;
    }
  };

  // 1. Header Banner
  doc.setFillColor(30, 27, 75); // Dark Indigo
  doc.rect(margin, y, contentWidth, 24, 'F');

  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  doc.text('INTERVIEW PERFORMANCE REPORT', margin + 6, y + 10);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.text('InterviewAI • Intelligent Performance Assessment', margin + 6, y + 17);

  y += 30;

  // 2. Candidate & Session Metadata Details
  doc.setTextColor(51, 65, 85); // Slate 700
  doc.setFontSize(9);

  const leftX = margin + 2;
  const rightX = margin + contentWidth / 2 + 4;

  doc.setFont('helvetica', 'bold');
  doc.text('Candidate:', leftX, y);
  doc.setFont('helvetica', 'normal');
  doc.text(candidateName || 'Candidate', leftX + 24, y);

  doc.setFont('helvetica', 'bold');
  doc.text('Target Role:', rightX, y);
  doc.setFont('helvetica', 'normal');
  doc.text(report.target_role || 'Software Developer', rightX + 26, y);

  y += 6;
  doc.setFont('helvetica', 'bold');
  doc.text('Interview Type:', leftX, y);
  doc.setFont('helvetica', 'normal');
  doc.text(`${report.interview_type || 'Technical'} (${report.difficulty || 'Intermediate'})`, leftX + 24, y);

  doc.setFont('helvetica', 'bold');
  doc.text('Date:', rightX, y);
  doc.setFont('helvetica', 'normal');
  const dateStr = report.created_at
    ? new Date(report.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    : new Date().toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  doc.text(dateStr, rightX + 26, y);

  y += 10;

  // 3. Overall Score Callout Box
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(margin, y, contentWidth, 22, 3, 3, 'FD');

  doc.setTextColor(79, 70, 229); // Indigo 600
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(20);
  doc.text(`${report.overall_score || 0.0} / 10`, margin + 6, y + 14);

  doc.setTextColor(30, 41, 59);
  doc.setFontSize(11);
  doc.text(`Overall Score: ${report.score_percentage || 0}%`, margin + 45, y + 10);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8.5);
  doc.setTextColor(100, 116, 139);
  const statusStr = (report.overall_score || 0) >= 8.0 ? 'Interview Ready • Strong Performance' : (report.overall_score || 0) >= 6.0 ? 'Competent • Minor Growth Areas' : 'Developing • Focus Practice Recommended';
  doc.text(statusStr, margin + 45, y + 16);

  doc.text(`Completion: ${report.completion_rate || 0}% (${report.evaluated_questions || 0}/${report.total_questions || 0} evaluated)`, margin + contentWidth - 60, y + 14);

  y += 28;

  // 4. Competency Breakdown
  doc.setTextColor(15, 23, 42);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.text('Rubric Performance Breakdown', margin, y);
  y += 5;

  const dimensions = [
    { label: 'Technical Accuracy', val: report.average_technical_accuracy !== null && report.average_technical_accuracy !== undefined ? `${report.average_technical_accuracy}/10` : 'N/A' },
    { label: 'Relevance', val: `${report.average_relevance || 0}/10` },
    { label: 'Completeness', val: `${report.average_completeness || 0}/10` },
    { label: 'Clarity', val: `${report.average_clarity || 0}/10` },
    { label: 'Communication', val: `${report.average_communication || 0}/10` },
  ];

  const colW = contentWidth / dimensions.length;
  doc.setFillColor(241, 245, 249);
  doc.rect(margin, y, contentWidth, 14, 'F');

  dimensions.forEach((dim, idx) => {
    const colX = margin + idx * colW + 2;
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(100, 116, 139);
    doc.text(dim.label, colX, y + 5);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.setTextColor(15, 23, 42);
    doc.text(dim.val, colX, y + 11);
  });

  y += 20;

  // 5. Strengths & Weak Areas Grid
  checkPageBreak(35);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.setTextColor(15, 23, 42);
  doc.text('Key Strengths & Growth Areas', margin, y);
  y += 6;

  const boxW = (contentWidth - 6) / 2;

  // Strengths Box
  doc.setFillColor(240, 253, 244); // Emerald 50
  doc.setDrawColor(187, 247, 208);
  doc.roundedRect(margin, y, boxW, 30, 2, 2, 'FD');

  doc.setTextColor(22, 101, 52); // Emerald 800
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.text('Demonstrated Strengths', margin + 4, y + 6);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  let sY = y + 12;
  (report.strong_areas || []).slice(0, 3).forEach((item) => {
    const lines = doc.splitTextToSize(`- ${item}`, boxW - 8);
    doc.text(lines, margin + 4, sY);
    sY += lines.length * 4.5;
  });

  // Weaknesses Box
  const weakX = margin + boxW + 6;
  doc.setFillColor(254, 243, 199); // Amber 50
  doc.setDrawColor(253, 230, 138);
  doc.roundedRect(weakX, y, boxW, 30, 2, 2, 'FD');

  doc.setTextColor(146, 64, 14); // Amber 800
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.text('Areas for Growth', weakX + 4, y + 6);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  let wY = y + 12;
  (report.weak_areas || []).slice(0, 3).forEach((item) => {
    const lines = doc.splitTextToSize(`- ${item}`, boxW - 8);
    doc.text(lines, weakX + 4, wY);
    wY += lines.length * 4.5;
  });

  y += 36;

  // 6. Actionable Recommendations
  if (report.top_improvements && report.top_improvements.length > 0) {
    checkPageBreak(25);
    doc.setFillColor(238, 242, 255); // Indigo 50
    doc.setDrawColor(224, 231, 255);
    doc.roundedRect(margin, y, contentWidth, 24, 2, 2, 'FD');

    doc.setTextColor(55, 48, 163); // Indigo 900
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.text('Key Actionable Recommendations', margin + 4, y + 6);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    let rY = y + 12;
    report.top_improvements.slice(0, 2).forEach((sug) => {
      const lines = doc.splitTextToSize(`* ${sug}`, contentWidth - 8);
      doc.text(lines, margin + 4, rY);
      rY += lines.length * 4.5;
    });

    y += 30;
  }

  // 7. Question-by-Question Evaluation Breakdown
  const rawEvaluations = report.evaluations;
  const evalList = Array.isArray(rawEvaluations)
    ? rawEvaluations
    : rawEvaluations && typeof rawEvaluations === 'object'
    ? Object.values(rawEvaluations)
    : [];

  if (evalList.length > 0) {
    checkPageBreak(20);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(15, 23, 42);
    doc.text('Evaluated Questions Breakdown', margin, y);
    y += 6;

    evalList.forEach((ev, idx) => {
      // Find question text if available
      const qNum = ev.question_number || idx + 1;
      let questionText = ev.question || '';
      if (!questionText && report.questions && report.questions[qNum - 1]) {
        questionText = report.questions[qNum - 1].question || '';
      }

      checkPageBreak(42);

      doc.setFillColor(255, 255, 255);
      doc.setDrawColor(226, 232, 240);
      doc.roundedRect(margin, y, contentWidth, 38, 2, 2, 'FD');

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(9);
      doc.setTextColor(79, 70, 229);
      doc.text(`Question #${qNum}  •  Score: ${ev.overall_score || 0}/10`, margin + 4, y + 6);

      // Question text
      let currY = y + 11;
      if (questionText) {
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8);
        doc.setTextColor(30, 41, 59);
        const qLines = doc.splitTextToSize(`Q: ${questionText}`, contentWidth - 8);
        doc.text(qLines.slice(0, 2), margin + 4, currY);
        currY += Math.min(qLines.length, 2) * 4;
      }

      // Candidate answer snippet
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7.5);
      doc.setTextColor(71, 85, 105);
      const ansLines = doc.splitTextToSize(`Candidate Answer: ${ev.candidate_answer || '(No answer recorded)'}`, contentWidth - 8);
      doc.text(ansLines.slice(0, 2), margin + 4, currY);
      currY += Math.min(ansLines.length, 2) * 4;

      // Evaluation Feedback / Strengths / Improvements
      doc.setTextColor(15, 23, 42);
      const feedbackStr = ev.summary || (ev.strengths?.length ? `Strengths: ${ev.strengths.join(', ')}` : '');
      if (feedbackStr) {
        const sumLines = doc.splitTextToSize(`Feedback: ${feedbackStr}`, contentWidth - 8);
        doc.text(sumLines.slice(0, 2), margin + 4, currY);
      }

      y += 42;
    });
  }

  // Footer on each page
  const totalPages = doc.internal.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(148, 163, 184);
    doc.text(
      `InterviewAI Performance Report  •  Page ${i} of ${totalPages}`,
      pageWidth / 2,
      pageHeight - 8,
      { align: 'center' }
    );
  }

  const roleName = (report.target_role || 'interview').toLowerCase().replace(/\s+/g, '_');
  const filename = `interview_report_${roleName}_${new Date().toISOString().slice(0, 10)}.pdf`;
  doc.save(filename);
};

