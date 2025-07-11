%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Class definition
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{INTERSPEECH2025_proceedings}[2025/01/06 Official Interspeech 2025 package]

\newif\if@print\@printfalse
\newif\if@abstract\@abstractfalse

\DeclareOption{onecolumn}{\OptionNotUsed}
\DeclareOption{print}{\@printtrue}
\DeclareOption{screen}{\@printfalse}
\DeclareOption{abstract}{\@abstracttrue}
\DeclareOption{noabstract}{\@abstractfalse}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax

\LoadClass{article}
\RequirePackage{hyperref}

%%% }}}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% General structure & formatting
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{


\RequirePackage{pdfpages}
% control margins & spacing
\RequirePackage{geometry}

% \geometry{
%     paperheight=303mm,
%     paperwidth=216mm,  % or: "paper=a4paper"
%     textheight=297mm,
%     textwidth=210mm,
%     margin=0pt,
%     includeheadfoot,
%     showframe=true,
%     showcrop=true
% }

\RequirePackage{setspace}
    \newlength{\footrectangleheight}

% Printing version or screen version
\if@print
    \RequirePackage{lscape}
    \setlength{\footrectangleheight}{15mm}
    \newcommand{\includeelements}[2][]{%
        \includepdf[#1,offset={0mm, 0mm}]{content-elements/print/#2}
    }

    \geometry{%
        paperwidth=216mm,
        paperheight=303mm,
        layoutvoffset=6mm,
        includeheadfoot,
        left=15mm,
        right=15mm,
        top=3mm,
        headheight=20mm, % as per the warning by fancyhdr
        bottom=15mm,
    }
\else

    \RequirePackage{pdflscape}
    \setlength{\footrectangleheight}{10mm}

    \geometry{%
        paperwidth=210mm,
        paperheight=297mm,
        left=15mm,
        right=15mm,
        top=40mm,
        headheight=20mm, % as per the warning by fancyhdr
        bottom=15mm,
    }

    \newcommand{\includeelements}[2][]{%
        \includepdf[#1]{content-elements/online/#2}
    }
\fi

% Font
\RequirePackage{lmodern}
\renewcommand{\sfdefault}{phv}
\renewcommand{\rmdefault}{ptm}
\renewcommand{\ttdefault}{pcr}
\renewcommand{\familydefault}{\sfdefault}

%%% }}}


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Colours and theme
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{

\RequirePackage[table]{xcolor}
\RequirePackage[most]{tcolorbox}

\input{theme/colours.tex}

%% Header, footers and overall page format
\RequirePackage{lastpage}
\RequirePackage{fancyhdr}
\renewcommand{\headrulewidth}{0pt}

\fancypagestyle{fancy}{%
  \fancyhf{} % clear all header and footer fields
  \fancyhead[LE]{
      \begin{tikzpicture}[overlay, remember picture]%
          % \node[anchor=north, inner sep=0,outer sep=0] at (current page.north){\includegraphics[width=\paperwidth]{theme/standard_header_left.pdf}};
      \end{tikzpicture}
  }
  \fancyhead[LO]{
      \begin{tikzpicture}[overlay, remember picture]%
          % \node[anchor=north, inner sep=0,outer sep=0] at (current page.north) {\includegraphics[width=\paperwidth]{theme/standard_header_right.pdf}};
      \end{tikzpicture}
  }
  \fancyfoot[C]{
      \begin{tikzpicture}[overlay, remember picture]%
          \fill[FooterBackgroundColour] (current page.south west)+(0,0) rectangle ($(current page.south east)+(,\footrectangleheight)$);
          \node[anchor=south, text=FooterForegroundColour, font=\large\bf, minimum size=\footrectangleheight] at (current page.south) {Page \thepage\ of \pageref*{LastPage}};
      \end{tikzpicture}
  }
}

\fancypagestyle{onlyfoot}{%
  \fancyhf{} % clear all header and footer fields
  \fancyfoot[C]{
      \begin{tikzpicture}[overlay, remember picture]%
          \fill[FooterBackgroundColour] (current page.south west)+(0mm,0) rectangle ($(current page.south east)+(0mm,\footrectangleheight)$);
          \node[anchor=south, text=FooterForegroundColour, font=\large\bf, minimum size=\footrectangleheight] at (current page.south) {Page \thepage\ of \pageref*{LastPage}};
      \end{tikzpicture}
  }
}

\fancypagestyle{plain}{%
  \fancyhf{} % clear all header and footer fields
}

% Graphics & Images
\RequirePackage{graphicx}
\RequirePackage{tikz} % Required for drawing custom shapes
\usetikzlibrary{shapes,shadows,calc}

% adds alignment keys to includegraphics
\RequirePackage[export]{adjustbox}

%%% }}}




%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Define some helper boxes
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{

% coloured boxes
\newtcbox{\inlinebox}[1][]{
    enhanced,
    box align=base,
    nobeforeafter,
    colback=DefaultBackgroundColour,
    colframe=DefaultForegroundColour,
    size=small,
    left=6pt,
    right=6pt,
    bottom=2pt,
    top=2pt,
    boxsep=2pt,
    #1
}
\newcommand{\mode}[1]{\inlinebox{\sc #1}}
\newtcbox{\timebox}[1][]{%
  on line,
  colframe=DefaultForegroundColour,
  colback=DefaultBackgroundColour,
  boxrule=0.5pt,
  arc=2pt,
  boxsep=0pt,
  left=6pt,
  right=6pt,
  top=3pt,
  bottom=2pt,
  #1
}
\newtcbox{\authorpapercolorbox}[1][]{
    on line,
    colframe=DefaultForegroundColour,
    colback=DefaultBackgroundColour,
    boxrule=0.5pt,
    arc=2pt,
    boxsep=0pt,
    left=6pt,
    right=6pt,
    top=3pt,
    bottom=2pt,
    #1
}
\newcommand{\authorpaperbox}[1]{%
    \authorpapercolorbox{\parbox{2.3cm}{#1}} % NOTE: size picked to fit the page in it
}
\newtcbox{\sectionbox}[1][]{
    enhanced,
    box align=base,
    nobeforeafter,
    colback=LinkColour,
    colframe=LinkColour,
    left=0pt,
    right=0pt,
    bottom=0pt,
    top=0pt,
    boxsep=4pt,
    %enlarge bottom initially by=4pt,
    #1
}


% Redefine the section headers
\RequirePackage{titlesec}
\titleformat*{\section}{\normalfont\Huge\bfseries\color{LinkColour}}

\newcommand{\colorsection}[1]{%
  \sectionbox{\parbox{\dimexpr\linewidth-4\fboxsep}{\color{white} #1}}
}
\titleformat{name=\subsection}[block]
  {\Large\bfseries}
  {}
  {0pt}
  {\colorsection}

%%% }}}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Define helper commands
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{

\RequirePackage{fontawesome}
\RequirePackage{xstring} %% NOTE: needed for IfStrEq

\newcommand{\pagetarget}[2]{%
  \phantomsection%
  \label{#1}%
  \hypertarget{#1}{#2}%
}

%% Command \paper takes 4 arguments:
%%    #1 the ID of the presentation in the session
%%    #2 the title
%%    #3 the authors
%%    #4 the abstract
%%    #5 the resource
\newcommand{\paper}[5]{%
    \begin{spacing}{1.3}
        \noindent\pagetarget{#1}{\timebox[colframe=red, colback=yellow!20]{ \textbf{#1} }\ {\large\textbf{#2} } }
    \end{spacing}
    \noindent{\normalfont\textit{#3}} \\
    %
    \ifx&#5&%
    \else
        \bigskip
        \par\noindent{\textbf{Resource:}} {\url{#5}}
    \fi
    %
    \bigskip
    %
    \if@abstract
        %
        \par\noindent \textbf{Abstract:}
        \par #4
        %
        \bigskip
    \fi
}

%% Command \presentation takes 5 arguments:
%%    #1 The type of presentation
%%    #2 the ID of the presentation in the session
%%    #3 the title
%%    #4 the authors
%%    #5 the presenters
%%    #6 the abstract
%%    #7 the resource
\newcommand{\presentation}[7]{%
    \begin{spacing}{1.3}
        \noindent\pagetarget{#2}{\timebox[#1]{ \textbf{#2} }\ {\large\textbf{#3} } }
    \end{spacing}
    \noindent{\normalfont\textit{#4}}
    %
    \bigskip
    %
    \par\noindent{\textbf{Presenter(s):} \normalfont\textit{#5}}
    %
    \ifx&#7&%
    \else
        \par\noindent{\textbf{Resource:}} {\url{#7}}
    \fi
    %
    \bigskip
    %
    \if@abstract
        %
        \par\noindent \textbf{Abstract:}
        \par #6
        %
        \bigskip
    \fi
}
%%% }}}
