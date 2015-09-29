
all:
	pdflatex report.tex
	bibtex report
	pdflatex report.tex
	pdflatex report.tex
clean:
	rm -f report.bbl report.blg report.log report.aux report.pdf
