"use client";

import React, { useState } from 'react';

export default function WorkflowPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [userRequest, setUserRequest] = useState("예산 5370원으로 20일치 영양가 높은 급식 메뉴를 계획해주세요");
  const [loading, setLoading] = useState(false);
  const [alternatives, setAlternatives] = useState([]);
  const [selectedAlternative, setSelectedAlternative] = useState(null);
  const [params, setParams] = useState({ days: 20, budget: 5370, calories: 900 });
  const [menuPlan, setMenuPlan] = useState([]);

  const steps = [
    { num: 1, title: "사용자 입력", icon: "👤" },
    { num: 2, title: "AI 대안 생성", icon: "✨" },
    { num: 3, title: "설정 조정", icon: "⚙️" },
    { num: 4, title: "메뉴 최적화", icon: "📅" }
  ];

  const mockAlternatives = [
    {
      id: 1,
      title: "영양 균형 중심 전략",
      description: "단백질, 비타민, 무기질의 완벽한 균형을 맞춘 성장기 학생 맞춤 식단",
      estimated_cost: 5200,
      target_calories: 920,
      features: ["고단백 식품", "비타민 A,C 강화", "칼슘/철분 최적화"],
      highlight: "영양소 완전 균형"
    },
    {
      id: 2,
      title: "경제성 우선 전략",
      description: "예산 내에서 최대한 다양하고 풍성한 메뉴를 제공하는 실용적 접근",
      estimated_cost: 4850,
      target_calories: 880,
      features: ["예산 절약", "메뉴 다양성", "대용량 조리"],
      highlight: "비용 효율성"
    },
    {
      id: 3,
      title: "선호도 중심 전략",
      description: "학생 기호도 조사를 바탕으로 한 높은 만족도와 섭취율을 목표로 하는 식단",
      estimated_cost: 5100,
      target_calories: 950,
      features: ["학생 선호 메뉴", "높은 섭취율", "트렌디한 퓨전"],
      highlight: "학생 만족도"
    }
  ];

  const handleGenerateAlternatives = async () => {
    setLoading(true);
    setTimeout(() => {
      setAlternatives(mockAlternatives);
      setCurrentStep(2);
      setLoading(false);
    }, 2000);
  };

  const handleSelectAlternative = async (id) => {
    setSelectedAlternative(id);
    setLoading(true);
    setTimeout(() => {
      setCurrentStep(3);
      setLoading(false);
    }, 1000);
  };

  const handleOptimization = async () => {
    setLoading(true);
    setCurrentStep(4);
    setTimeout(() => {
      const mockMenu = Array.from({ length: params.days }, (_, i) => ({
        day: i + 1,
        rice: i % 3 === 0 ? "잡곡밥" : "현미밥",
        soup: ["김치찌개", "된장국", "미역국"][i % 3],
        side1: ["불고기", "생선구이", "닭갈비"][i % 3],
        side2: ["시금치나물", "콩나물무침"][i % 2],
        side3: ["김치", "깍두기"][i % 2],
        snack: i % 7 === 2 ? "사과" : "(없음)",
        day_cost: Math.floor(Math.random() * 1000 + 4500),
        day_kcal: Math.floor(Math.random() * 200 + 800)
      }));
      setMenuPlan(mockMenu);
      setLoading(false);
    }, 3000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-green-50 to-blue-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-green-600 bg-clip-text text-transparent">
            🍽️ 급식 메뉴 최적화 시스템
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
        
        {/* Step 1: 사용자 입력 */}
        {currentStep === 1 && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl flex items-center justify-center">
                <span className="text-2xl">👤</span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">1단계: 사용자 입력</h2>
                <p className="text-gray-600">급식 계획에 대한 요구사항을 작성해주세요</p>
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
                    AI가 전략을 생성하고 있습니다...
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-xl">✨</span>
                    대안 생성하기
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
                <h2 className="text-xl font-bold text-gray-900">2단계: AI 대안 생성</h2>
                <p className="text-gray-600">3가지 전략 중 하나를 선택해주세요</p>
              </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              {alternatives.map((alt) => (
                <div
                  key={alt.id}
                  className={`border-2 rounded-2xl p-6 cursor-pointer transition-all transform hover:scale-105 hover:shadow-xl ${
                    selectedAlternative === alt.id
                      ? 'border-blue-500 bg-blue-50 shadow-lg'
                      : 'border-gray-200 bg-white hover:border-blue-300'
                  }`}
                  onClick={() => handleSelectAlternative(alt.id)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-bold text-gray-900 text-lg">{alt.title}</h3>
                    {selectedAlternative === alt.id && (
                      <span className="text-2xl">✅</span>
                    )}
                  </div>
                  
                  <p className="text-gray-600 text-sm mb-4">{alt.description}</p>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">예상 비용</span>
                      <span className="font-semibold text-green-600">{alt.estimated_cost.toLocaleString()}원</span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">목표 칼로리</span>
                      <span className="font-semibold text-orange-600">{alt.target_calories}kcal</span>
                    </div>

                    {alt.features && (
                      <div className="pt-3 border-t border-gray-100">
                        <p className="text-xs text-gray-500 mb-2">주요 특징</p>
                        <div className="flex flex-wrap gap-1">
                          {alt.features.slice(0, 3).map((feature, idx) => (
                            <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                              {feature}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {alt.highlight && (
                      <div className="mt-3 p-2 bg-yellow-50 rounded-lg border border-yellow-200">
                        <p className="text-xs font-medium text-yellow-800">
                          🌟 {alt.highlight}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {loading && (
              <div className="mt-6 text-center">
                <div className="inline-flex items-center gap-2 text-blue-600">
                  <div className="w-5 h-5 border-2 border-blue-600/30 border-t-blue-600 rounded-full animate-spin"></div>
                  선택하신 전략을 분석하고 있습니다...
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 3: 설정 조정 */}
        {currentStep === 3 && selectedAlternative && (
          <div className="space-y-6">
            {/* Agent-based 분석 결과 */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
              <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <span className="text-xl">🤖</span>
                Agent-based 비교 분석 결과
              </h3>
              
              <div className="bg-gradient-to-r from-blue-50 to-green-50 rounded-xl p-6">
                <h4 className="font-semibold text-gray-900 mb-3">
                  선택된 전략: {alternatives.find(a => a.id === selectedAlternative)?.title}
                </h4>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">85</div>
                    <div className="text-sm text-gray-600">🥗 영양사 에이전트</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">80</div>
                    <div className="text-sm text-gray-600">💰 경제 에이전트</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">75</div>
                    <div className="text-sm text-gray-600">😊 학생 에이전트</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">82</div>
                    <div className="text-sm text-gray-600">⚙️ 운영 에이전트</div>
                  </div>
                </div>
                
                <div className="p-4 bg-white/50 rounded-lg">
                  <p className="text-sm text-gray-700 mb-2">
                    <strong>🤖 Agent 합의:</strong> 영양사 에이전트와 경제 에이전트가 동시에 추천
                  </p>
                  <p className="text-sm text-gray-700">
                    <strong>추천 이유:</strong> 영양 균형이 우수하고 예산 준수율이 높음
                  </p>
                </div>
              </div>
            </div>

            {/* 설정 조정 */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">⚙️</span>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">3단계: 설정 조정</h2>
                  <p className="text-gray-600">파라미터를 조정하고 최적화를 실행하세요</p>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900">실시간 설정 조정</h3>
                  
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
                </div>

                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900">자연어로 변경하기</h3>
                  
                  <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-100">
                    <p className="text-sm text-gray-600 mb-3">예시:</p>
                    <div className="text-xs text-gray-500 space-y-1">
                      <div>• "가격 500원 올려줘"</div>
                      <div>• "예산을 6000원으로 설정해줘"</div>
                    </div>
                  </div>

                  <textarea
                    className="w-full h-20 p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 resize-none"
                    placeholder="자연어로 설정을 변경해보세요..."
                  />
                  
                  <button
                    className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium hover:from-purple-600 hover:to-pink-600 transition-all"
                  >
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-xl">⚡</span>
                      자연어 처리하기
                    </div>
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
                      최적화 실행 중...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-xl">📅</span>
                      메뉴 최적화 실행
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
                  <h3 className="text-xl font-bold text-gray-900 mb-2">GA 알고리즘 실행 중...</h3>
                  <p className="text-gray-600 mb-4">유전자 알고리즘으로 최적의 메뉴 조합을 찾고 있습니다</p>
                  <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-500 to-green-500 h-full animate-pulse" style={{width: '60%'}}></div>
                  </div>
                  <p className="text-sm text-gray-500 mt-2">평균 소요 시간: 30초 - 1분</p>
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
                      <h2 className="text-xl font-bold text-gray-900">4단계: 최적화 완료!</h2>
                      <p className="text-gray-600">{params.days}일간의 최적 급식 메뉴가 생성되었습니다</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100">
                      <div className="text-2xl font-bold text-green-600">{params.days}일</div>
                      <div className="text-sm text-gray-600">총 급식일</div>
                    </div>
                    <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4 border border-blue-100">
                      <div className="text-2xl font-bold text-blue-600">
                        {menuPlan.reduce((sum, day) => sum + day.day_cost, 0).toLocaleString()}원
                      </div>
                      <div className="text-sm text-gray-600">총 급식비</div>
                    </div>
                    <div className="bg-gradient-to-br from-orange-50 to-yellow-50 rounded-xl p-4 border border-orange-100">
                      <div className="text-2xl font-bold text-orange-600">
                        {Math.round(menuPlan.reduce((sum, day) => sum + day.day_kcal, 0) / menuPlan.length)}
                      </div>
                      <div className="text-sm text-gray-600">평균 칼로리</div>
                    </div>
                    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-100">
                      <div className="text-2xl font-bold text-purple-600">A+</div>
                      <div className="text-sm text-gray-600">영양 등급</div>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <button
                      onClick={() => alert(`📄 가정통신문이 생성됩니다!\n${params.days}일 급식 메뉴표가 포함됩니다.`)}
                      className="flex-1 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-xl font-medium hover:from-indigo-600 hover:to-purple-600 transition-all"
                    >
                      <div className="flex items-center justify-center gap-2">
                        <span className="text-xl">📄</span>
                        가정통신문 생성
                      </div>
                    </button>
                    <button
                      onClick={() => alert('메뉴표를 다운로드합니다!')}
                      className="flex-1 py-3 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-xl font-medium hover:from-green-600 hover:to-teal-600 transition-all"
                    >
                      <div className="flex items-center justify-center gap-2">
                        <span className="text-xl">📊</span>
                        메뉴표 다운로드
                      </div>
                    </button>
                  </div>
                </div>

                {/* 메뉴 결과 테이블 */}
                <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-white/50 shadow-xl">
                  <h3 className="text-lg font-bold text-gray-900 mb-6">생성된 급식 메뉴표</h3>
                  
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
                            <td className="px-4 py-3">{day.rice}</td>
                            <td className="px-4 py-3">{day.soup}</td>
                            <td className="px-4 py-3">{day.side1}</td>
                            <td className="px-4 py-3">{day.side2}</td>
                            <td className="px-4 py-3">{day.side3}</td>
                            <td className="px-4 py-3 text-blue-600 font-medium">{day.snack}</td>
                            <td className="px-4 py-3 text-center font-medium">{Math.round(day.day_kcal)}</td>
                            <td className="px-4 py-3 text-center font-medium">{day.day_cost.toLocaleString()}원</td>
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
                </div>
              </>
            ) : null}
          </div>
        )}

        {/* 새로 시작하기 버튼 */}
        {currentStep === 4 && menuPlan.length > 0 && (
          <div className="text-center pt-8">
            <button
              onClick={() => {
                setCurrentStep(1);
                setAlternatives([]);
                setSelectedAlternative(null);
                setMenuPlan([]);
                setUserRequest("예산 5370원으로 20일치 영양가 높은 급식 메뉴를 계획해주세요");
              }}
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
              🍽️ 급식줍쇼
            </h3>
            <p className="text-gray-600 mb-4">AI 기반 학교급식 메뉴 최적화 시스템</p>
            <div className="flex justify-center gap-8 text-sm text-gray-500">
              <span>• LLM 전략 생성</span>
              <span>• Agent-based 분석</span>
              <span>• 자연어 파라미터 조정</span>
              <span>• GA 메뉴 최적화</span>
            </div>
            <div className="mt-8 text-xs text-gray-400">
              © 2024 급식줍쇼. AI로 더 건강한 급식을 만들어갑니다.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}