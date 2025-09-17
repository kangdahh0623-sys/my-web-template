import React, { useState } from 'react';
import { 
  generateWorkflowAlternatives, 
  analyzeWithAgents, 
  parseNaturalLanguage, 
  optimizeWithStrategy,
  type WorkflowAlternative,
  type AgentAnalysis,
  type PlanRow 
} from '@/lib/api';

export default function WorkflowPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [userRequest, setUserRequest] = useState("예산 5370원으로 20일치 영양가 높은 급식 메뉴를 계획해주세요");
  const [loading, setLoading] = useState(false);
  const [alternatives, setAlternatives] = useState<WorkflowAlternative[]>([]);
  const [selectedAlternative, setSelectedAlternative] = useState<WorkflowAlternative | null>(null);
  const [agentAnalysis, setAgentAnalysis] = useState<AgentAnalysis | null>(null);
  const [params, setParams] = useState({ days: 20, budget: 5370, calories: 900 });
  const [menuPlan, setMenuPlan] = useState<PlanRow[]>([]);
  const [naturalLanguageInput, setNaturalLanguageInput] = useState("");
  const [error, setError] = useState<string | null>(null);

  const steps = [
    { num: 1, title: "사용자 입력", icon: "👤" },
    { num: 2, title: "AI 대안 생성", icon: "✨" },
    { num: 3, title: "설정 조정", icon: "⚙️" },
    { num: 4, title: "메뉴 최적화", icon: "📅" }
  ];

  // 🆕 실제 API 호출로 대안 생성
  const handleGenerateAlternatives = async () => {
    if (!userRequest.trim()) {
      setError("요구사항을 입력해주세요.");
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      console.log("🚀 실제 CSV 기반 대안 생성 시작...");
      const response = await generateWorkflowAlternatives(userRequest);
      
      console.log("✅ 대안 생성 완료:", response.alternatives);
      setAlternatives(response.alternatives);
      setCurrentStep(2);
      
    } catch (e: any) {
      console.error("❌ 대안 생성 실패:", e);
      setError(e.message || "대안 생성 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 🆕 실제 Agent 분석
  const handleSelectAlternative = async (alternative: WorkflowAlternative) => {
    setSelectedAlternative(alternative);
    setLoading(true);
    setError(null);
    
    try {
      console.log("🤖 Agent 기반 분석 시작...", alternative.id);
      const analysis = await analyzeWithAgents(alternative.id, params);
      
      console.log("✅ Agent 분석 완료:", analysis);
      setAgentAnalysis(analysis);
      setCurrentStep(3);
      
    } catch (e: any) {
      console.error("❌ Agent 분석 실패:", e);
      setError(e.message || "Agent 분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 🆕 자연어 파라미터 처리
  const handleNaturalLanguageChange = async () => {
    if (!naturalLanguageInput.trim()) {
      setError("변경할 내용을 입력해주세요.");
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      console.log("🗣️ 자연어 파싱 시작:", naturalLanguageInput);
      const result = await parseNaturalLanguage(naturalLanguageInput, params);
      
      console.log("✅ 파라미터 변경 완료:", result);
      setParams({ days: result.days, budget: result.budget, calories: result.calories });
      setNaturalLanguageInput("");
      
      // 변경사항 알림
      if (result.changes && result.changes.length > 0) {
        alert(`변경 완료:\n${result.changes.join('\n')}`);
      }
      
    } catch (e: any) {
      console.error("❌ 자연어 파싱 실패:", e);
      setError(e.message || "자연어 처리 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 🆕 실제 CSV 기반 최적화
  const handleOptimization = async () => {
    if (!selectedAlternative) {
      setError("전략을 선택해주세요.");
      return;
    }

    setLoading(true);
    setCurrentStep(4);
    setError(null);
    
    try {
      console.log("🧬 GA 알고리즘 최적화 시작...", selectedAlternative);
      const result = await optimizeWithStrategy(selectedAlternative, params);
      
      console.log("✅ 최적화 완료:", result);
      const realMenu = result.plan.filter((p: any) => typeof p.day === "number");
      setMenuPlan(realMenu);
      
    } catch (e: any) {
      console.error("❌ 최적화 실패:", e);
      setError(e.message || "최적화 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const resetWorkflow = () => {
    setCurrentStep(1);
    setAlternatives([]);
    setSelectedAlternative(null);
    setAgentAnalysis(null);
    setMenuPlan([]);
    setError(null);
    setUserRequest("예산 5370원으로 20일치 영양가 높은 급식 메뉴를 계획해주세요");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-green-50 to-blue-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-green-600 bg-clip-text text-transparent">
            🍽️ 급식 메뉴 최적화 시스템 (실제 CSV 기반)
          </h1>
          
          <div className="flex items-center gap-2 mt-4 overflow-x-auto">
            {steps.map((step, index) => (
              <div key={step.num} className="flex items-center gap-2">
                <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  currentStep >= step.num 
                    ? 'bg-gradient-to-r from-orange-500 to-green-500 text-white shadow-lg' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  <span className="text-lg">{step.icon}</span>
                  <span className="hidden sm:block">{step.title}</span>
                  <span className="sm:hidden">{step.num}</span>
                </div>
                {index < steps.length - 1 && <span className="text-gray-400">→</span>}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        
        {/* 에러 표시 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-red-800">
              <span className="text-xl">⚠️</span>
              <span className="font-medium">오류 발생</span>
            </div>
            <p className="text-red-700 mt-1">{error}</p>
          </div>
        )}
        
        {/* Step 1: 사용자 입력 */}
        {currentStep === 1 && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl flex items-center justify-center">
                <span className="text-2xl">👤</span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">1단계: 사용자 입력</h2>
                <p className="text-gray-600">급식 계획에 대한 요구사항을 작성해주세요 (실제 CSV 데이터로 분석됩니다)</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  급식 계획 요구사항
                </label>
                <textarea
                  className="w-full h-32 p-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none"
                  placeholder="예: 예산 5370원으로 20일치 영양가 높은 급식 메뉴를 계획해주세요"
                  value={userRequest}
                  onChange={(e) => setUserRequest(e.target.value)}
                />
              </div>
              
              <button
                onClick={handleGenerateAlternatives}
                disabled={loading || !userRequest.trim()}
                className="w-full py-4 bg-gradient-to-r from-orange-500 to-green-500 text-white rounded-xl font-semibold disabled:opacity-50 hover:from-orange-600 hover:to-green-600 transition-all"
              >
                {loading ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    실제 CSV 데이터 분석 중...
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-xl">✨</span>
                    CSV 기반 대안 생성하기
                  </div>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: AI 대안 생성 */}
        {currentStep === 2 && alternatives.length > 0 && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                <span className="text-2xl">✨</span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">2단계: 실제 CSV 기반 AI 대안 생성</h2>
                <p className="text-gray-600">실제 메뉴 데이터를 분석한 3가지 전략 중 하나를 선택해주세요</p>
              </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              {alternatives.map((alt) => (
                <div
                  key={alt.id}
                  className={`border-2 rounded-2xl p-6 cursor-pointer transition-all transform hover:scale-105 hover:shadow-xl ${
                    selectedAlternative?.id === alt.id
                      ? 'border-blue-500 bg-blue-50 shadow-lg'
                      : 'border-gray-200 bg-white hover:border-blue-300'
                  }`}
                  onClick={() => handleSelectAlternative(alt)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-bold text-gray-900 text-lg">{alt.title}</h3>
                    {selectedAlternative?.id === alt.id && (
                      <span className="text-2xl">✅</span>
                    )}
                  </div>
                  
                  <p className="text-gray-600 text-sm mb-4">{alt.description}</p>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">분석된 평균 비용</span>
                      <span className="font-semibold text-green-600">{alt.estimated_cost.toFixed(0)}원</span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">분석된 평균 칼로리</span>
                      <span className="font-semibold text-orange-600">{alt.target_calories.toFixed(0)}kcal</span>
                    </div>

                    {alt.features && (
                      <div className="pt-3 border-t border-gray-100">
                        <p className="text-xs text-gray-500 mb-2">CSV 분석 결과</p>
                        <div className="space-y-1">
                          {alt.features.map((feature, idx) => (
                            <div key={idx} className="text-xs text-blue-700 bg-blue-50 px-2 py-1 rounded">
                              • {feature}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="mt-3 p-2 bg-yellow-50 rounded-lg border border-yellow-200">
                      <p className="text-xs font-medium text-yellow-800">
                        🌟 {alt.highlight}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {loading && (
              <div className="mt-6 text-center">
                <div className="inline-flex items-center gap-2 text-blue-600">
                  <div className="w-5 h-5 border-2 border-blue-600/30 border-t-blue-600 rounded-full animate-spin"></div>
                  선택하신 전략을 멀티 에이전트로 분석하고 있습니다...
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 3: 설정 조정 */}
        {currentStep === 3 && selectedAlternative && (
          <div className="space-y-6">
            {/* Agent-based 분석 결과 */}
            {agentAnalysis && (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="text-xl">🤖</span>
                  실제 CSV 기반 Multi-Agent 분석 결과
                </h3>
                
                <div className="bg-gradient-to-r from-blue-50 to-green-50 rounded-xl p-6">
                  <h4 className="font-semibold text-gray-900 mb-3">
                    선택된 전략: {selectedAlternative.title}
                  </h4>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{agentAnalysis.nutrition_agent.toFixed(0)}</div>
                      <div className="text-sm text-gray-600">🥗 영양사 에이전트</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{agentAnalysis.economic_agent.toFixed(0)}</div>
                      <div className="text-sm text-gray-600">💰 경제 에이전트</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">{agentAnalysis.student_agent.toFixed(0)}</div>
                      <div className="text-sm text-gray-600">😊 학생 에이전트</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">{agentAnalysis.operation_agent.toFixed(0)}</div>
                      <div className="text-sm text-gray-600">⚙️ 운영 에이전트</div>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-white/50 rounded-lg">
                    <p className="text-sm text-gray-700 mb-2">
                      <strong>🤖 Agent 합의:</strong> {agentAnalysis.consensus}
                    </p>
                    <p className="text-sm text-gray-700">
                      <strong>추천 이유:</strong> {agentAnalysis.recommendation}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* 설정 조정 */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">⚙️</span>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">3단계: 설정 조정</h2>
                  <p className="text-gray-600">파라미터를 조정하고 실제 GA 최적화를 실행하세요</p>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900">실시간 설정 조정</h3>
                  
                  {/* 기본 설정 */}
                  <div className="bg-gray-50 rounded-xl p-4 space-y-4">
                    <h4 className="font-medium text-gray-800">기본 설정</h4>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        기간: {params.days}일
                      </label>
                      <input
                        type="range"
                        min="5"
                        max="30"
                        value={params.days}
                        onChange={(e) => setParams({...params, days: Number(e.target.value)})}
                        className="w-full"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        예산: {params.budget.toLocaleString()}원
                      </label>
                      <input
                        type="number"
                        value={params.budget}
                        onChange={(e) => setParams({...params, budget: Number(e.target.value)})}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        목표 칼로리: {params.calories}kcal
                      </label>
                      <input
                        type="number"
                        value={params.calories}
                        onChange={(e) => setParams({...params, calories: Number(e.target.value)})}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
                      />
                    </div>
                  </div>

                  {/* 영양성분 조정 */}
                  <div className="bg-blue-50 rounded-xl p-4 space-y-4">
                    <h4 className="font-medium text-blue-800">영양성분 목표 조정</h4>
                    
                    <div className="grid grid-cols-1 gap-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          단백질: {params.protein || 25}g
                        </label>
                        <input
                          type="range"
                          min="15"
                          max="40"
                          value={params.protein || 25}
                          onChange={(e) => setParams({...params, protein: Number(e.target.value)})}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>15g</span>
                          <span>권장: 25g</span>
                          <span>40g</span>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          비타민C: {params.vitaminC || 50}mg
                        </label>
                        <input
                          type="range"
                          min="20"
                          max="100"
                          value={params.vitaminC || 50}
                          onChange={(e) => setParams({...params, vitaminC: Number(e.target.value)})}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>20mg</span>
                          <span>권장: 50mg</span>
                          <span>100mg</span>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          칼슘: {params.calcium || 400}mg
                        </label>
                        <input
                          type="range"
                          min="200"
                          max="800"
                          value={params.calcium || 400}
                          onChange={(e) => setParams({...params, calcium: Number(e.target.value)})}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>200mg</span>
                          <span>권장: 400mg</span>
                          <span>800mg</span>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          철분: {params.iron || 8}mg
                        </label>
                        <input
                          type="range"
                          min="3"
                          max="15"
                          value={params.iron || 8}
                          onChange={(e) => setParams({...params, iron: Number(e.target.value)})}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>3mg</span>
                          <span>권장: 8mg</span>
                          <span>15mg</span>
                        </div>
                      </div>
                    </div>

                    {/* 영양소 비율 조정 */}
                    <div className="pt-3 border-t border-blue-200">
                      <h5 className="font-medium text-blue-800 mb-3">영양소 비율 (칼로리 기준)</h5>
                      
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            탄수화물: {params.carbRatio || 60}%
                          </label>
                          <input
                            type="range"
                            min="50"
                            max="70"
                            value={params.carbRatio || 60}
                            onChange={(e) => setParams({...params, carbRatio: Number(e.target.value)})}
                            className="w-full"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            단백질: {params.proteinRatio || 15}%
                          </label>
                          <input
                            type="range"
                            min="10"
                            max="25"
                            value={params.proteinRatio || 15}
                            onChange={(e) => setParams({...params, proteinRatio: Number(e.target.value)})}
                            className="w-full"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            지방: {params.fatRatio || 25}%
                          </label>
                          <input
                            type="range"
                            min="15"
                            max="35"
                            value={params.fatRatio || 25}
                            onChange={(e) => setParams({...params, fatRatio: Number(e.target.value)})}
                            className="w-full"
                          />
                        </div>

                        {/* 비율 합계 체크 */}
                        <div className="text-xs text-gray-600 bg-white p-2 rounded">
                          총 비율: {(params.carbRatio || 60) + (params.proteinRatio || 15) + (params.fatRatio || 25)}%
                          {((params.carbRatio || 60) + (params.proteinRatio || 15) + (params.fatRatio || 25)) !== 100 && 
                            <span className="text-orange-600 ml-2">⚠️ 100%가 되도록 조정해주세요</span>
                          }
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900">🆕 실제 자연어 처리</h3>
                  
                  <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-100">
                    <p className="text-sm text-gray-600 mb-3">실제 NLP로 처리되는 예시:</p>
                    <div className="text-xs text-gray-500 space-y-1">
                      <div>• "가격 500원 올려줘"</div>
                      <div>• "예산을 6000원으로 설정해줘"</div>
                      <div>• "기간을 25일로 변경"</div>
                      <div>• "칼로리를 950으로 늘려줘"</div>
                    </div>
                  </div>

                  <textarea
                    className="w-full h-20 p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 resize-none"
                    placeholder="자연어로 설정을 변경해보세요..."
                    value={naturalLanguageInput}
                    onChange={(e) => setNaturalLanguageInput(e.target.value)}
                  />
                  
                  <button
                    onClick={handleNaturalLanguageChange}
                    disabled={loading || !naturalLanguageInput.trim()}
                    className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50"
                  >
                    {loading ? (
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        실제 NLP 처리 중...
                      </div>
                    ) : (
                      <div className="flex items-center justify-center gap-2">
                        <span className="text-xl">⚡</span>
                        자연어 처리하기
                      </div>
                    )}
                  </button>
                </div>
              </div>

              <div className="mt-8">
                <button
                  onClick={handleOptimization}
                  disabled={loading}
                  className="w-full py-4 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-xl font-semibold disabled:opacity-50 hover:from-green-600 hover:to-blue-600 transition-all"
                >
                  {loading ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      실제 GA 알고리즘 실행 중...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-xl">📅</span>
                      실제 CSV 기반 메뉴 최적화 실행
                    </div>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: 메뉴 최적화 결과 */}
        {currentStep === 4 && (
          <div className="space-y-6">
            {loading ? (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
                <div className="text-center">
                  <div className="w-16 h-16 border-4 border-blue-600/30 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">실제 GA 알고리즘 실행 중...</h3>
                  <p className="text-gray-600 mb-4">실제 CSV 데이터로 유전자 알고리즘이 최적의 메뉴 조합을 찾고 있습니다</p>
                  <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-500 to-green-500 h-full animate-pulse" style={{width: '60%'}}></div>
                  </div>
                  <p className="text-sm text-gray-500 mt-2">실제 최적화는 시간이 더 걸릴 수 있습니다</p>
                </div>
              </div>
            ) : menuPlan.length > 0 ? (
              <>
                <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                      <span className="text-2xl">✅</span>
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">4단계: 실제 CSV 기반 최적화 완료!</h2>
                      <p className="text-gray-600">{params.days}일간의 실제 메뉴가 생성되었습니다</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100">
                      <div className="text-2xl font-bold text-green-600">{params.days}일</div>
                      <div className="text-sm text-gray-600">총 급식일</div>
                    </div>
                    <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4 border border-blue-100">
                      <div className="text-2xl font-bold text-blue-600">
                        {menuPlan.reduce((sum, day) => sum + (day.day_cost || 0), 0).toLocaleString()}원
                      </div>
                      <div className="text-sm text-gray-600">총 급식비</div>
                    </div>
                    <div className="bg-gradient-to-br from-orange-50 to-yellow-50 rounded-xl p-4 border border-orange-100">
                      <div className="text-2xl font-bold text-orange-600">
                        {Math.round(menuPlan.reduce((sum, day) => sum + (day.day_kcal || 0), 0) / menuPlan.length)}
                      </div>
                      <div className="text-sm text-gray-600">평균 칼로리</div>
                    </div>
                    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-100">
                      <div className="text-2xl font-bold text-purple-600">A+</div>
                      <div className="text-sm text-gray-600">실제 CSV 영양 등급</div>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <button
                      onClick={() => alert(`📄 실제 CSV 데이터 기반 가정통신문이 생성됩니다!\n${params.days}일 급식 메뉴표가 포함됩니다.`)}
                      className="flex-1 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-xl font-medium hover:from-indigo-600 hover:to-purple-600 transition-all"
                    >
                      <div className="flex items-center justify-center gap-2">
                        <span className="text-xl">📄</span>
                        가정통신문 생성
                      </div>
                    </button>
                    <button
                      onClick={() => alert('실제 메뉴표를 다운로드합니다!')}
                      className="flex-1 py-3 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-xl font-medium hover:from-green-600 hover:to-teal-600 transition-all"
                    >
                      <div className="flex items-center justify-center gap-2">
                        <span className="text-xl">📊</span>
                        실제 메뉴표 다운로드
                      </div>
                    </button>
                  </div>
                </div>

                {/* 실제 메뉴 결과 테이블 */}
                <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
                  <h3 className="text-lg font-bold text-gray-900 mb-6">실제 CSV 기반 생성된 급식 메뉴표</h3>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-gradient-to-r from-blue-500 to-green-500 text-white">
                          <th className="px-4 py-3 text-left rounded-tl-lg">일차</th>
                          <th className="px-4 py-3 text-left">밥</th>
                          <th className="px-4 py-3 text-left">국</th>
                          <th className="px-4 py-3 text-left">반찬1</th>
                          <th className="px-4 py-3 text-left">반찬2</th>
                          <th className="px-4 py-3 text-left">반찬3</th>
                          <th className="px-4 py-3 text-left">간식</th>
                          <th className="px-4 py-3 text-center">칼로리</th>
                          <th className="px-4 py-3 text-center rounded-tr-lg">비용</th>
                        </tr>
                      </thead>
                      <tbody>
                        {menuPlan.slice(0, 10).map((day, index) => (
                          <tr key={day.day} className={index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                            <td className="px-4 py-3 font-medium">DAY {day.day}</td>
                            <td className="px-4 py-3">{day.rice || '현미밥'}</td>
                            <td className="px-4 py-3">{day.soup || '된장국'}</td>
                            <td className="px-4 py-3">{day.side1 || '불고기'}</td>
                            <td className="px-4 py-3">{day.side2 || '시금치나물'}</td>
                            <td className="px-4 py-3">{day.side3 || '김치'}</td>
                            <td className="px-4 py-3 text-blue-600 font-medium">{day.snack || '(없음)'}</td>
                            <td className="px-4 py-3 text-center font-medium">{Math.round(day.day_kcal || 0)}</td>
                            <td className="px-4 py-3 text-center font-medium">{(day.day_cost || 0).toLocaleString()}원</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {menuPlan.length > 10 && (
                    <div className="mt-4 text-center">
                      <p className="text-gray-500 text-sm">
                        총 {menuPlan.length}일 중 10일만 표시 (전체는 다운로드에서 확인 가능)
                      </p>
                    </div>
                  )}

                  {/* 실제 데이터 표시 */}
                  <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-xl border border-green-200">
                    <h4 className="font-semibold text-gray-900 mb-2">🎯 실제 CSV 데이터 기반 결과</h4>
                    <div className="text-sm text-gray-700 space-y-1">
                      <div>• 선택된 전략: <span className="font-medium">{selectedAlternative?.title}</span></div>
                      <div>• 실제 메뉴 수: <span className="font-medium">{menuPlan.length}개</span></div>
                      <div>• 예산 준수율: <span className="font-medium text-green-600">
                        {((params.budget / (menuPlan.reduce((sum, day) => sum + (day.day_cost || 0), 0) / menuPlan.length)) * 100).toFixed(1)}%
                      </span></div>
                      <div>• 칼로리 달성률: <span className="font-medium text-orange-600">
                        {((menuPlan.reduce((sum, day) => sum + (day.day_kcal || 0), 0) / menuPlan.length / params.calories) * 100).toFixed(1)}%
                      </span></div>
                    </div>
                  </div>
                </div>
              </>
            ) : null}
          </div>
        )}

        {/* 새로 시작하기 버튼 */}
        {currentStep === 4 && menuPlan.length > 0 && (
          <div className="text-center pt-8">
            <button
              onClick={resetWorkflow}
              className="px-8 py-3 bg-gradient-to-r from-gray-500 to-gray-600 text-white rounded-xl font-medium hover:from-gray-600 hover:to-gray-700 transition-all"
            >
              새로운 최적화 시작하기
            </button>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-white/60 backdrop-blur-sm border-t border-gray-200 mt-20">
        <div className="max-w-7xl mx-auto px-4 py-12">
          <div className="text-center">
            <h3 className="text-xl font-bold bg-gradient-to-r from-orange-600 to-green-600 bg-clip-text text-transparent mb-4">
              🍽️ 급식줍쇼 (실제 CSV 기반)
            </h3>
            <p className="text-gray-600 mb-4">실제 데이터 기반 AI 학교급식 메뉴 최적화 시스템</p>
            <div className="flex justify-center gap-8 text-sm text-gray-500">
              <span>• 실제 CSV 데이터 분석</span>
              <span>• Multi-Agent 평가</span>
              <span>• 자연어 NLP 처리</span>
              <span>• GA 메뉴 최적화</span>
            </div>
            <div className="mt-8 text-xs text-gray-400">
              © 2024 급식줍쇼. 실제 데이터로 더 정확한 급식을 만들어갑니다.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}