all: report.pdf

report.pdf: report.tex report.bbl
	pdflatex report.tex

report.bbl: report.aux report.bib
	bibtex report

report.aux: report.tex
	pdflatex report.tex

clean:
	rm -f report.bbl report.blg report.log report.aux report.out report.pdf
