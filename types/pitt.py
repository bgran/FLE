# Progressive Inquiry knowledge types by:
#   Kai Hakkarainen
#   Minna Lakkala
#   Pirita Seitamaa-Hakkarainen
#   Samu Mielonen
#   Teemu Leinonen
#
name='Progressive Inquiry'
language='English'
description= \
"""Learning can be seen as a research practice aiming to solve a group's
understanding of a subject by creating a visible discussion of research
challenges, theories, scientific facts and summaries. The process aims to
be progressive in its approach by starting from initial problems and ideas
of the students and then becoming progressively more challenging through
creation of more elaborate problems, theories and research practices.

The Progressive Inquiry knowledge types aim to scaffold a learning community
to follow the process of setting up research problems, making current
knowledge visible and working from there to deepen the understanding on
the issue by creating discussion notes. The reading and writing of these
notes is seen as the key momentum of the process, helping learners to
structure their ideas based on the principle of scientific research.
"""
types=(
        {'id': 'problem',
         'name': 'Problem',
         'starting_phrase':
"""I would like to find out why/how...
I am interested in studying why/how...""",
         'description':\
"""Your study problem in research. The learning process aims at answering
to the problems presented by the students. The purpose of defining a
problem statement is to explicate your learning goals, to explain your
research interests and also to introduce the questions that are
directing your inquiry. After critically viewing the present working
theories and by introducing new deepening knowledge to the discussion,
also new subordinate problems can be defined.""",
         'checklist':
"""Are you introducing the problems that <b>you are interested in</b> studying?

Are you explaining your <b>research interests</b>?

Give explanations to your problem in another note.""",
         'colour': "tt_yellowlt",
         'icon': "ui/images/types/coi/problem.gif",
         },
        {'id': 'my_expl',
         'name': 'My Explanation',
         'starting_phrase':
"""I think that...
I believe that...""",
        'description':
""" My Explanation presents your own conceptions (hypothesis, theory,
explanation, interpretation) about the problems presented by yourself or
some of your fellow students. "My Explanation" is not necessarily well
defined or articulated early in the inquiry process. However, it is
crucial that the explication of your explanations evolves during the
process and your working theories become more refined and developed.""",
         'checklist':
"""Are you presenting <b>your own thinking</b> (notion, hypothesis, theory, explanation or interpretation)?

<b>Don't finalize</b> your explanation. Post more elaborated versions later.

If you have knowledge from an information source, you should write a "Scientific explanation".""",
         'colour': "tt_aqua",
         'icon': "ui/images/types/coi/work_th.gif",
        },
        {'id': 'sci_expl',
        'name': 'Scientific Explanation',
        'starting_phrase': """I have found some information...""",
        'description':
"""Scientific Explanation presents some scientific findings or other
knowledge that you have sought. Under  Scientific Explanation  you may
brings to the discussion some new points of view or otherwise helps the
inquiry process to continue. It differs from your own explanation (My
Explanation) in that it represents knowledge produced by others,
generally some authority or expert. My Explanations should be your own
ideas where as Scientific Explanation is some ones else idea in the area
in concern.""",
         'checklist':
"""Are you including <b>information provided by an expert</b> in the domain?

Does the explanation <b>connect to the problems and explanations</b> you have posted?

Remember to mention <b>where you found the information</b> (book, article, web site, TV programme, lecture, discussion).""",
         'colour': "tt_orangelt",
         'icon': "ui/images/types/coi/deep_kn.gif",
         },
##         {'id': 'comment',
##         'name': 'Comment',
##         'starting_phrase': """Comment""",
##         'description':\
## """Your more general comment to the inquiry process. The comment can be
## presented for example to someone else's working theory. A comment is
## used to ask for clarification, more thorough explanation, opinion and so
## on. With a comment message you can also provide help for other learners'
## problem-solving process.""",
##          'colour': "tt_bluelt",
##         'icon': "ui/images/types/coi/comment.gif",
##         },
        {'id': 'evaluation',
        'name': 'Evaluation of the Process',
        'starting_phrase': """I think that our ideas...
I think that our learning process...""",
        'description':\
"""Your comment that focuses on the inquiry process and its methods
instead of the process outcomes - meta-comment. With a "Evaluation of
the Process" you may evaluate e.g. whether the process is progressing in
the desired direction, whether appropriate methods are used, how sharing
of tasks and inquiry process is accomplished among the members of the
learning community.""",
         'checklist':
"""Are you talking about <b>organizing the work</b> of your group?

Have you expressed <b>your opinion</b> on how the learning process is advancing?

Are you <b>sharing tasks</b> or <b>discussing the methods</b> used?""",
         'colour': "tt_purple",
        'icon': "ui/images/types/coi/meta_co.gif",
        },
        {'id': 'summary',
        'name': 'Summary',
        'starting_phrase': """We have learned that...
We came up with the conclusion that...""",
        'description':\
"""With a summary you draw pieces of the discussion together and provide
inferences based on the discussion in the Knowledge Building. The
summary may aim at identifying a new Course Context or may reflect the
views of the writer on the progression of the inquiry learning process.""",
         'checklist':
"""Have you <b>reviewed all the notes</b> in the thread?

Are you <b>drawing together discussions</b> carried out in the thread?

Are you <b>explaining what you've learned</b> about the topics that were initially stated?""",
         'colour': "tt_greenlt",
        'icon': "ui/images/types/coi/summary.gif",
        },
)
thread_start=('problem',)
# With what you can respond.
# For a better example, please consult cvs repo!

relations={}
tt_ids = [x['id'] for x in types]
for type in types:
        relations[type['id']] = tt_ids

# EOF
