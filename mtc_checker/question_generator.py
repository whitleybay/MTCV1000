
import random

class MTCQuestionGenerator:
    def __init__(self):
        self.questions = []
        self.practice_questions = []
        self.NUM_QUESTIONS = 25
        self.NUM_PRACTICE_QUESTIONS = 3
        self.multiplicands_range = list(range(2, 13))
        self.focus_tables = {6: 0, 7: 0, 8: 0, 9: 0, 12: 0}
        self.min_focus_questions_per_table = 2

    def _is_duplicate(self, op1, op2, existing_list):
        for q_detail in existing_list:
            if (q_detail['op1'] == op1 and q_detail['op2'] == op2) or                (q_detail['op1'] == op2 and q_detail['op2'] == op1):
                return True
        return False

    def _generate_single_question(self, allowed_op1_list, allowed_op2_list, existing_list):
        attempts = 0
        while attempts < 100: # Safety break
            op1 = random.choice(allowed_op1_list)
            op2 = random.choice(allowed_op2_list)
            if not self._is_duplicate(op1, op2, existing_list):
                return op1, op2
            attempts += 1
        # Fallback if unique not found easily (should be rare with broad ranges)
        return random.choice(allowed_op1_list), random.choice(allowed_op2_list)


    def generate_test_questions(self):
        self.questions = []
        current_focus_counts = {k: 0 for k in self.focus_tables}

        # 1. Ensure minimum from focus tables
        for table_num in self.focus_tables.keys():
            while current_focus_counts[table_num] < self.min_focus_questions_per_table:
                # One operand is the focus table, the other can be any from the range
                op1, op2 = self._generate_single_question([table_num], self.multiplicands_range, self.questions)
                
                # Ensure the generated question is not a duplicate in self.questions
                is_new = True
                for q_item in self.questions:
                    if (q_item['op1'] == op1 and q_item['op2'] == op2) or                        (q_item['op1'] == op2 and q_item['op2'] == op1):
                        is_new = False
                        break
                if not is_new: # Try again if it's a duplicate
                    continue

                self.questions.append({'op1': op1, 'op2': op2, 'answer': op1 * op2})
                
                # Update counts for all focus tables involved in this question
                if op1 in current_focus_counts:
                    current_focus_counts[op1] += 1
                if op2 in current_focus_counts: # (op1 != op2 is implicitly handled by how counts are incremented)
                    current_focus_counts[op2] += 1
                
                if len(self.questions) >= self.NUM_QUESTIONS: # Stop if we've already filled up
                    break
            if len(self.questions) >= self.NUM_QUESTIONS:
                break
        
        # 2. Fill remaining questions
        while len(self.questions) < self.NUM_QUESTIONS:
            op1, op2 = self._generate_single_question(self.multiplicands_range, self.multiplicands_range, self.questions)
            self.questions.append({'op1': op1, 'op2': op2, 'answer': op1 * op2})

        # Ensure exactly NUM_QUESTIONS, shuffle if over, add if under (though less likely now)
        if len(self.questions) > self.NUM_QUESTIONS:
            random.shuffle(self.questions)
            self.questions = self.questions[:self.NUM_QUESTIONS]
        
        # Final shuffle
        random.shuffle(self.questions)
        return self.questions

    def generate_practice_questions(self):
        self.practice_questions = []
        practice_multiplicands = [2, 3, 4, 5, 10] # Easier tables
        all_current_questions = self.questions + self.practice_questions # Check against main test too
        
        while len(self.practice_questions) < self.NUM_PRACTICE_QUESTIONS:
            op1, op2 = self._generate_single_question(practice_multiplicands, practice_multiplicands, all_current_questions)
            self.practice_questions.append({'op1': op1, 'op2': op2, 'answer': op1 * op2})
            all_current_questions.append({'op1': op1, 'op2': op2}) # Add to check list

        random.shuffle(self.practice_questions)
        return self.practice_questions

    def get_full_test_set(self):
        main_q = self.generate_test_questions() # Generate main first
        prac_q = self.generate_practice_questions() # Then practice (checks against main)
        return {'practice': prac_q, 'main': main_q}
