import CompanyCard from './CompanyCard'
import MetricsTable from './MetricsTable'
import PriceChart from './PriceChart'
import SentimentBadge from './SentimentBadge'
import ComparisonTable from './ComparisonTable'
import SourceAttribution from './SourceAttribution'
import { formatDate } from '../../utils/formatters'

function Section({ section }) {
  const { type, title, content, data } = section

  const renderContent = () => {
    switch (type) {
      case 'company_overview':
        return (
          <div className="space-y-4">
            {data && Object.keys(data).length > 0 && <CompanyCard data={data} />}
            {content && <p className="text-sm text-gray-700 leading-relaxed">{content}</p>}
          </div>
        )

      case 'financial_metrics':
        return (
          <div className="space-y-4">
            {content && <p className="text-sm text-gray-700 leading-relaxed">{content}</p>}
            {data && Object.keys(data).length > 0 && <MetricsTable data={data} />}
          </div>
        )

      case 'price_chart':
        return (
          <div className="space-y-4">
            {data && <PriceChart data={data} symbol={data.symbol} />}
            {content && <p className="text-sm text-gray-700 leading-relaxed">{content}</p>}
          </div>
        )

      case 'comparison_table':
        return (
          <div className="space-y-4">
            {content && <p className="text-sm text-gray-700 leading-relaxed">{content}</p>}
            {data && <ComparisonTable data={data} />}
          </div>
        )

      case 'news_sentiment':
        return (
          <div className="space-y-3">
            {content && <p className="text-sm text-gray-700 leading-relaxed">{content}</p>}
            {data?.articles?.map((article, i) => (
              <div key={i} className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 text-sm leading-snug">{article.title}</p>
                    {article.description && (
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">{article.description}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-2">
                      {article.source_name} · {article.published_at ? formatDate(article.published_at) : ''}
                    </p>
                  </div>
                  <div className="shrink-0">
                    <SentimentBadge label={article.sentiment?.label} />
                  </div>
                </div>
              </div>
            ))}
            {data?.sentiment_summary && (
              <div className="bg-gray-50 rounded-lg p-3 flex gap-4 text-sm">
                <span className="text-green-600 font-medium">↑ {data.sentiment_summary.positive} positive</span>
                <span className="text-red-600 font-medium">↓ {data.sentiment_summary.negative} negative</span>
                <span className="text-gray-500">{data.sentiment_summary.neutral} neutral</span>
              </div>
            )}
          </div>
        )

      case 'risk_assessment':
        return (
          <div className="space-y-2">
            {content && (
              <div className="text-sm text-gray-700 leading-relaxed space-y-1">
                {content.split('\n').filter(Boolean).map((line, i) => (
                  <div key={i} className="flex gap-2">
                    <span className="text-orange-500 mt-0.5 shrink-0">⚠</span>
                    <span>{line.replace(/^[-•*]\s*/, '')}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )

      case 'document_insights':
        return (
          <div className="space-y-3">
            {data?.results?.map((doc, i) => (
              <div key={i} className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded font-medium">
                    {doc.metadata?.company || 'Document'}
                  </span>
                  <span className="text-xs text-amber-600">{doc.metadata?.doc_type}</span>
                  <span className="text-xs text-gray-400">{doc.metadata?.filing_date}</span>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{doc.content}</p>
              </div>
            ))}
            {content && <p className="text-sm text-gray-700 leading-relaxed">{content}</p>}
          </div>
        )

      default:
        return content ? <p className="text-sm text-gray-700 leading-relaxed">{content}</p> : null
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
        <h3 className="font-semibold text-gray-800">{title}</h3>
      </div>
      <div className="p-5">{renderContent()}</div>
    </div>
  )
}

export default function ResultsRenderer({ report }) {
  if (!report) return null

  return (
    <div className="space-y-4">
      {/* Executive Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
        <h2 className="text-lg font-bold text-gray-900 mb-2">{report.title}</h2>
        <p className="text-sm text-gray-700 leading-relaxed">{report.summary}</p>
        {report.companies_analyzed?.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {report.companies_analyzed.map((sym) => (
              <span key={sym} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-mono font-semibold">
                {sym}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Sections */}
      {report.sections?.map((section, i) => (
        <Section key={i} section={section} />
      ))}

      {/* Sources */}
      {report.sources?.length > 0 && <SourceAttribution sources={report.sources} />}
    </div>
  )
}
