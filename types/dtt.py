# Progressive Design knowledge types by:
#   Pirita Seitamaa-Hakkarainen
#   Asta Raami
#   Kai Hakkarainen
#   Samu Mielonen
#   Teemu Leinonen
#
name='Design Thinking Types'
language='English'
description= \
"""The design process is seen as a cyclical and iterative process of manipulating
visual and technical design ideas. The most important part of the design
process is the analysis of the design context, design constraints and
generating new design ideas. The use of the Progressive Design Thinking
Types based on the model of the collaborative design process. (Pirita Seitamaa-Hakkarainen)"""
types=({'id': 'context',
        'name': 'Design Context',
        'starting_phrase':"""In this process we should design...""",
        'description':\
"""The environment forms part of the context of a design challenge. Design context is typically specified in a design brief or in a negotiation with a client. The design brief does not completely specify all the requirements, guidelines and wishes for the product to be designed. It is often a general and vague description of the desired product, giving only partial information about the user, the purpose of the product or resources. These are external constraints for the design process.

However, during the design process the designers have to specify the given  design constraints and sometimes even modify them. The new information may also change the design context as the designer develops more internal constraints for the design. The analysis of design context is one of the most important aspects of the design  process.""",
        'checklist':
"""Does the note define some <b>requirements, guidelines or wishes</b> related to the design project?

Does the note <b>clarify your design task</b>?

Does the note describe some <b>design constraints</b>?""",
        'colour': "tt_orangelt",
        'icon': "ui/images/types/dtt/orange.gif",
        },
        {'id': 'challenge',
        'name': 'Design Challenge',
        'starting_phrase': """The challenge in this design is...""",
        'description':\
"""Design challenge is your own definition of the problem that design needs to solve. During the design process design challenge can be divided into more specific design tasks (i.e. sub-problems). Design task is a smaller sub division of the Design challenge which can be solved on it's own and which is a step closer to the actual implementation than the challenge.

Design challenge and design tasks are tied to the principal design ideas and design context. Design tasks aim at helping designers find solutions to the main goal. Moreover, new information can emerge from the solutions of new specific design tasks.""",
        'checklist':
"""Does the note present <b>design problem or sub-problem</b>?

Does the note define a <b>design task</b>?""",
         'colour': "tt_aqua",
        'icon': "ui/images/types/dtt/aqua.gif",
        },
        {'id': 'idea',
        'name': 'My Design Idea',
        'starting_phrase': """My solution to this is...
My idea is...""",
        'description':\
"""A design idea represents your own solution to the design challenge at hand. It is a sort of first sketch of a design idea - a visualisation of the idea or a verbal description of the main functions of a solution. Design idea can be conceptual or conctre. The different type of visual ideas (e.g. visual sketches) can be further labelled as thinking sketch, prescriptive sketch or final alternative. A design idea is not necessarily well defined or articulated early in the design process.

However, it is crucial to understand that by creating design ideas visible to yourself and others during the design process these ideas become more refined and developed. Thus, you should avoid going straight from the first sketch to a final alternative, but rather make most all your sketches and design  ideas visible to others.""",
        'checklist':
"""Does the note describe your <b>own solution</b> to the design task or problem?

Do you present <b>your own idea</b> in the note?""",
         'colour': "tt_yellowlt",
        'icon': "ui/images/types/dtt/yellow.gif",
        },
        {'id': 'info',
        'name': 'New Information',
        'starting_phrase': """I have found some information...""",
        'description':\
"""A design idea is not necessarily well defined early in the design process. Further, there are probably lot of open questions related to design context and design challenges. Searching and providing new information and knowledge is important for further development of design ideas.

Providing new information related to design constraints, the design ideas become more refined and developed. One can gather crucial new information by interviewing users and analysing context or earlier design approaches by others.""",
        'checklist':
"""Does the note present some <b>new information</b> related to the design task?

Remember to mention the source where you got the new information:

- by <b>interviewing users</b>
- by <b>analysing the design context</b>?
- <b>studying earlier design solutions</b> of others.""",
         'colour': "tt_bluelt",
        'icon': "ui/images/types/dtt/blue.gif",
        },
        {'id': 'eval',
        'name': 'Evaluating an Idea',
        'starting_phrase': """In this design idea I like... because
In this design idea I don't like... because""",
        'description':\
"""The evaluation of design ideas and design processes is crucial for collaborative designing. You should give feedback about design ideas to your fellow designers. It is useful to note that sometimes the solution further refines the design problem and vice versa, making it worthwhile to go visit and reflect your earlier design context analysis and ideas again.""",
        'checklist':
"""Does the note <b>give feedback</b> related to your fellow designers' ideas?

You may <b>evaluate your own ideas</b>, too.""",
         'colour': "tt_purple",
        'icon': "ui/images/types/dtt/purple.gif",
        },
        {'id': 'org',
        'name': 'Organizing the Process',
        'starting_phrase': """I think we should proceed by/with...""",
        'description':\
"""In a collaborative design process it is important to make general plans and division of labour between designers. With an "Organizing the Process" you may make plans on how to proceed, evaluate (e.g. whether the process is progressing in the desired direction, whether appropriate methods are used), how sharing of tasks should be done and how design process is co-ordinated among the members of the design community.""",
        'checklist':
"""Does the note suggest some way to <b>organize the design process</b>?

Does the note consider questions such as <b>timetable, deadlines, meetings, roles, ToDo-lists etc.</b>?""",
         'colour': "tt_greenlt",
        'icon': "ui/images/types/dtt/green.gif",
        },
        {'id': 'sum',
        'name': 'Summary',
        'starting_phrase': """The conclusion that we came up in this design...""",
        'description':\
"""With a summary you draw pieces of the design ideas together and propose a solution to the design challenge or a sub-task. A Summary can pull together various pieces, such as design context, working ideas or design process, in order to illustrate how those concepts belong together.

It also may reflect the summarized views of the collaborative design process by reflecting different aspects, which have been considered under discussion. Final summary pulls together sub-tasks and their solutions to a single unified solution that aims to solve the original main design challenge.""",
        'checklist':
"""Does the note contain a <b>conclusion or design decision</b> that is made?

You may illustrate your note with <b>a sketch that pulls together different design ideas</b> presented during the study.""",
         'colour': "tt_white",
        'icon': "ui/images/types/dtt/white.gif",
        },
)
# What is user to start threads.
thread_start=('context',)

# All types may be used to reply to any type.
relations={}
tt_ids = [x['id'] for x in types]
for type in types:
        relations[type['id']] = tt_ids

# EOF
